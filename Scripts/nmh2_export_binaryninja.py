# By MekuCube
# Operates in 3 steps: Collects all types relevant to a keyword (like 'Travis'), sorts those types based on dependency, and then exports those types to a C header.
# Tested on Binary Ninja Personal 2.4.2846

import re, inspect, time, cProfile, pstats, json

def GetTypeByName(InString):
	if GetTypeByName.cache == None:
		GetTypeByName.cache = bv.types
	if InString in GetTypeByName.cache:
		return GetTypeByName.cache[InString]
	# Debug
	if False:
		print("Failed to find type '" + str(InString) + "'", end="")
		PossibleMatches = []
		# Figure out intention
		if False:
			for TypeIt in bv.types:
				if InString in str(TypeIt):
					PossibleMatches.append(TypeIt)
			if len(PossibleMatches) > 0:
				print(", did you mean", end="")
				IsFirst = True
				for TypeIt in PossibleMatches:
					if IsFirst == True:
						IsFirst = False
					else:
						print(" /", end="")	
					print(" '" + str(TypeIt) + "'", end="")
				print("?", end="")
			print(" [via "+str(inspect.stack()[1][3])+"]")
		print("")

GetTypeByName.cache = None

def GetParentNameSpaceFromType(InType):
	
	NameSpaces = GetNameSpacesFromType(InType)
	if NameSpaces == None or len(NameSpaces) <= 0:
		return None
	return NameSpaces[-1]

def HasValidParentNameSpace(InType):
	ParentNameSpace = GetParentNameSpaceFromType(InType)
	if ParentNameSpace == None:
		return False
	return GetTypeByName(ParentNameSpace) != None

def GetFunctionNameWithoutNameSpace(InType):
	FunctionName = str(InType.name)
	FunctionName = FunctionName.split("?", 1)[-1] # Starts at "?"
	FunctionName = FunctionName.split("@")[0]
	return FunctionName

# Given a type returns a list of parent namespaces as strings (['A', 'A::B']
def GetNameSpacesFromType(InType):
	if hasattr(InType, 'calc_namespaces'):
		return InType.calc_namespaces
	Input = str(InType)
	if isinstance(InType, binaryninja.function.Function):
		FunctionName = GetFunctionNameWithoutNameSpace(InType)
		# TODO: Comment
		Input = Input.split(FunctionName + "(")[0]
		Input = Input.split(" ")[-1]
		Input = Input + FunctionName
	else:
		# Check for template
		Input = Input.split("<")[0]
	Result = GetNameSpacesFromString(Input)
	setattr(InType, 'calc_namespaces', Result)
	return Result

# Given a string (A::B::C) returns a list of parent namespaces as strings (['A', 'A::B']
def GetNameSpacesFromString(InString):
	split = InString.split("::")
	if len(split) <= 1:
		return None
	# Remove type itself
	split = split[:-1]
	if " " in split[0]:
		split[0] = split[0].split(" ")[-1]
	if " " in split[-1]:
		split[-1] = split[-1].split(" ")[0]
	if len(split) > 1:
		for i in range(len(split)-1, 0, -1):
			for j in range(i-1, -1, -1):
				split[i] = split[j] + "::" + split[i]
	return split

# HACK: True if in array (you can't trust "if TypeIt in visited_types", it only checks str(type))
def IsInListPure(InType, InList):
	for TypeIt in InList:
		if TypeEqualsPure(InType, TypeIt):
			return True
	return False

# HACK: True equal (you can't trust "if TypeIt == TypeIt2", it only checks str(type))
def TypeEqualsPure(InType, TypeIt):
	if TypeIt != InType:
		return False
	if id(TypeIt) != id(InType):
		return False
	if isinstance(InType, binaryninja.types.Type):
		if TypeIt.type_class != InType.type_class:
			return False
		if TypeIt.element_type != InType.element_type:
			return False
	return True

# Returns true if any added to the visited_types array
def VisitType(InType, visited_types, VisitOuterNameSpace = True, VisitPointers = True):
	if InType == None:
		return False
	TypeStr = str(InType)
	if "std::_Func_impl_no_alloc" in TypeStr:
		return False
	if "std::tuple<" in TypeStr:
		return False
	#if isinstance(InType, binaryninja.types.Type):
	#	print("Pre-Visit: '" + TypeStr + "' (" + str(InType.type_class) + ")")
	#else:
	#	print("Pre-Visit: '" + TypeStr + "'")
	# Already visited
	if IsInListPure(InType, visited_types):
		#print("Already visited: '" + TypeStr + "' ("+str(TypeIt) + ")")
		return False
	# Don't visit native types
	if isinstance(InType, binaryninja.types.Type):
		if InType.type_class == TypeClass.NamedTypeReferenceClass:
			TypeNameStr = str(InType.named_type_reference.name)
			if TypeNameStr != None:
				TypeNameObject = GetTypeByName(TypeNameStr)
				if VisitType(TypeNameObject, visited_types, VisitOuterNameSpace, VisitPointers):
					return True
			#print("Failed to resolve NamedTypeReferenceClass '" + str(InType) + "' (" + TypeNameStr + ")")
			return False
		if InType.type_class == TypeClass.PointerTypeClass:
			IsProperPointer = TypeStr.endswith("*")
			if IsProperPointer and not VisitPointers:
				return False
			if InType.element_type != None:
				return VisitType(InType.element_type, visited_types, VisitOuterNameSpace, VisitPointers)
			return False
		if not VisitPointers and TypeStr.endswith("*"):
			return False
		if InType.type_class != TypeClass.StructureTypeClass and InType.type_class != TypeClass.EnumerationTypeClass:
			#print("Skipped '" + str(InType) + "' due to type_class '" + str(InType.type_class) + "'")
			return False
	#print("Visit: '" + TypeStr + "'")
	# Mark as visited
	visited_types.append(InType)
	# Visit outer namespaces
	if VisitOuterNameSpace:
		NameSpaces = GetNameSpacesFromType(InType)
		if NameSpaces != None:
			for NameSpace in NameSpaces:
				VisitType(GetTypeByName(NameSpace), visited_types, VisitOuterNameSpace, VisitPointers)
	if isinstance(InType, binaryninja.types.Type):
		# Visit struct members
		if InType.structure != None:
			#print("Visit: '" + str(InType) + "' (" + str(len(InType.structure.members)) + " members)")
			for MemberIt in InType.structure.members:
				if MemberIt.type != None and MemberIt.type != InType:
					#print("   - Trying to visit member type: '" + str(MemberIt.type) + "' (" + str(MemberIt.type.type_class) + ")")
					VisitType(MemberIt.type, visited_types, VisitOuterNameSpace, VisitPointers)
				if VisitPointers and MemberIt.type.element_type != None and MemberIt.type.element_type != InType:
					#print("   - Trying to visit element type: '" + str(MemberIt.type))
					VisitType(MemberIt.type.element_type, visited_types, VisitOuterNameSpace, VisitPointers)
		# Visit parameters
		if InType.parameters != None:
			for ParameterIt in InType.parameters:
				if ParameterIt.type != None and ParameterIt.type != InType:
					VisitType(ParameterIt.type, visited_types, VisitOuterNameSpace, VisitPointers)
		# Visit element type
		if InType.element_type != None and InType.element_type != InType:
			VisitType(InType.element_type, visited_types, VisitOuterNameSpace, VisitPointers)
		# Named type
		if InType.named_type_reference != None and InType.named_type_reference.type_class != None:
			NamedType = InType.named_type_reference.name
			NamedTypeRef = GetTypeByName(str(NamedType))
			if NamedTypeRef != None and NamedTypeRef != InType:
				VisitType(NamedTypeRef, visited_types, VisitOuterNameSpace, VisitPointers)
	# Visit function
	if isinstance(InType, binaryninja.function.Function):
		# return type
		if InType.return_type != InType:
			VisitType(InType.return_type, visited_types, VisitOuterNameSpace, VisitPointers)
		DemangledType, DemangledName = demangle_ms(Architecture["x86"], InType.name, False)
		if DemangledType != None and DemangledType != InType:
			VisitType(DemangledType, visited_types, VisitOuterNameSpace, VisitPointers)
		# Function type
		if InType.function_type != None and InType.function_type != InType:
			VisitType(InType.function_type, visited_types, VisitOuterNameSpace, VisitPointers)
		# Parameter vars
		#print("Visiting function vars for '" + str(InType) + "'")
		for VarIt in InType.parameter_vars:
			VisitType(VarIt.type, visited_types, VisitOuterNameSpace, VisitPointers)
	return True

# Collects all types that will be used
def CollectTypes(visited_types, AllowHeaders):
	for FunctionIt in bv.functions:
		FunctionStr = str(FunctionIt)
		ShouldIgnore = AllowHeaders != None and len(AllowHeaders) > 0
		if AllowHeaders != None:
			for AllowIt in AllowHeaders:
				if AllowIt in FunctionStr:
					ShouldIgnore = False
		if not ShouldIgnore:
			VisitType(FunctionIt, visited_types, True, True)
	for TypeIt in bv.types:
		TypeStr = str(TypeIt)
		ShouldIgnore = AllowHeaders != None and len(AllowHeaders) > 0
		if AllowHeaders != None:
			for AllowIt in AllowHeaders:
				if AllowIt in TypeStr:
					ShouldIgnore = False
		if not ShouldIgnore:
			VisitType(TypeIt, visited_types, True, True)
	# Filter (TODO: Doesn't seem to work)
	TypesToIgnore = ["class CStlVector<", "class EE::StringBase<", "enum EE::StringBase<", "class EE::String", "struct D3D11", "struct ID3D11", "struct IUnknown", "struct EE::OptListNode<", "class FkStlVector<", "class FkStlList<", "class tiMatrix", "struct CONTAINER<", "::<lambda_", "class std::" ]
	filtered_types = []
	for TypeIt in visited_types:
		if isinstance(TypeIt, binaryninja.types.Type):
			# We only care about structs & enums (functions are not Type)
			if TypeIt.type_class != TypeClass.StructureTypeClass and TypeIt.type_class != TypeClass.EnumerationTypeClass:
				continue
			IsIgnoreType = False
			for TypeToIgnore in TypesToIgnore:
				if str(TypeIt).startswith(TypeToIgnore):
					IsIgnoreType = True
					break
			if IsIgnoreType:
				continue
		filtered_types.append(TypeIt)
	visited_types = filtered_types
	#if True:
	if len(visited_types) < 10:
		print("Visited types: ", end="")
		IsFirst = True
		for TypeIt in visited_types:
			if IsFirst == True:
				IsFirst = False
			else:
				print(", ", end="")
			print(str(TypeIt), end="")
		print("")

def GetTypesInNameSpace(NameSpaceRoot, AllNonRootTypes):
	OutResult = []
	RootStr = str(NameSpaceRoot)
	
	for TypeIt in AllNonRootTypes:
		if TypeIt == NameSpaceRoot:
			continue
		if TypeIt.calc_parentnamespace_type == None:
			continue
		if not TypeEqualsPure(TypeIt.calc_parentnamespace_type, NameSpaceRoot):
			continue
		# Check if its a named type
		if isinstance(TypeIt, binaryninja.types.Type) and TypeIt.named_type_reference != None and TypeIt.named_type_reference.type_class != None:
			NamedType = TypeIt.named_type_reference.name
			NamedTypeRef = GetTypeByName(str(NamedType))
			if NamedTypeRef != None and NamedTypeRef != TypeIt and NamedTypeRef != NameSpaceRoot:
				OutResult.append(NamedTypeRef)
				continue
		OutResult.append(TypeIt)
	return OutResult

def FunctionIsStatic(InType):
	IsObjectInstance = False
	ParentNameSpaceStr = GetParentNameSpaceFromType(InType)
	i = 0
	for VarIt in InType.parameter_vars:
		VariableName = str(VarIt.name)
		if ParentNameSpaceStr != None and VariableName == "this" and i == 0:
			IsObjectInstance = True
		i = i + 1
	return ParentNameSpaceStr != None and not IsObjectInstance

def IsNativeType(InType):
	if InType.type_class == TypeClass.IntegerTypeClass:
		return InType.type_class
	if InType.type_class == TypeClass.FloatTypeClass:
		return InType.type_class
	if InType.type_class == TypeClass.BoolTypeClass:
		return InType.type_class
	if InType.type_class == TypeClass.EnumerationTypeClass:
		return InType.type_class
	if InType.type_class == TypeClass.VoidTypeClass:
		return InType.type_class
	if InType.type_class == TypeClass.PointerTypeClass and InType.element_type != None:
		return IsNativeType(InType.element_type)
	return None

# Returns string error
def CanTypeExportInFunction(InType):
	if InType == None:
		return None
	TypeStr = str(InType)
	# We convert this to std::string so its fine
	if TypeStr == "char const*":
		return None
	# We convert this to std::string so its fine
	if TypeStr == "char wchar_t*":
		return None
	TypeNameStr = "None"
	if InType.type_class != None:
		TypeNameStr = str(InType.type_class)
	# Can't export pointer to native types
	if InType.type_class != None and InType.type_class == TypeClass.PointerTypeClass and InType.element_type != None and IsNativeType(InType.element_type):
		return "Can't export pointer to native type '" + TypeStr + "' ["+TypeNameStr+"] in LuaBridge"
	if TypeStr.endswith("**"):
		return "Can't export pointer to pointer '" + TypeStr + "' ["+TypeNameStr+"] in LuaBridge"
	if TypeStr.endswith("&"):
		return "Can't export & pointer '" + TypeStr + "' ["+TypeNameStr+"] in LuaBridge"
	if TypeStr == "void*":
		return "Can't export void pointer '" + TypeStr + "' ["+TypeNameStr+"] in LuaBridge"
	if "(void*)" in TypeStr:
		return "Can't export delegate '" + TypeStr + "' ["+TypeNameStr+"] in LuaBridge"
	return None

def ExportFiller(InType, SessionData, indent, StartOffset, EndOffset, file):
	if StartOffset >= EndOffset:
		return
	TypeStr = str(InType)
	# See if there's any definitions in this filler
	if "json" in SessionData and "Extend" in SessionData["json"] and TypeStr in SessionData["json"]["Extend"] and "Definitions" in SessionData["json"]["Extend"][TypeStr]:
		DefinitionDict = SessionData["json"]["Extend"][TypeStr]["Definitions"]
		for i in range(0, len(DefinitionDict.items())):
			EarliestKey = None
			EarliestOffset = None
			EarliestSize = None
			for Key,Value in DefinitionDict.items():
				SplitKey = Key.split(",")
				if len(SplitKey) != 2:
					continue
				StartOffsetIt = int(SplitKey[0], 16)
				if StartOffsetIt < StartOffset or StartOffsetIt >= EndOffset:
					continue
				SizeIt = None
				if "0x" in SplitKey[1]:
					SizeIt = int(SplitKey[1], 16)
				else:
					SizeIt = int(SplitKey[1])
				if SizeIt == None or SizeIt <= 0:
					continue
				if EarliestOffset != None and EarliestOffset <= StartOffsetIt:
					continue
				EarliestKey = Key
				EarliestOffset = StartOffsetIt
				EarliestSize = SizeIt
			if EarliestKey == None:
				break
			else:
				# Insert definition
				ExportFiller(InType, SessionData, indent, StartOffset, EarliestOffset, file)
				#print("StartOffset -> EarliestOffset ["+str(hex(StartOffset))+"] = ", end="")
				StartOffset = EarliestOffset
				#print("[" + str(hex(StartOffset))+"]")
				print("	"*indent + "// <Custom definition, offset "+str(hex(StartOffset)) + ">", file=file)
				print("	"*indent + DefinitionDict[EarliestKey], file=file)
				print("", file=file)
				#print(str(EarliestSize))
				#print("StartOffset += Size ["+str(hex(StartOffset))+"] = ", end="")
				StartOffset = StartOffset + EarliestSize
				#print("[" + str(hex(StartOffset))+"]")
	if StartOffset >= EndOffset:
		return
	print("	"*indent + "// <Unidentified data segment, offset "+str(hex(StartOffset)) + ">", file=file)
	print("	"*(indent-1) + "private:", file=file)
	print("	"*indent + "char _UnidentifiedData_"+str(StartOffset).replace("0x","")+"[" + str(EndOffset - StartOffset) + "];", file=file)
	print("", file=file)
	print("	"*(indent-1) + "public:", file=file)

def ExportType(InType, AllTypes, ExportedTypes, SessionData, ExportedLuaBindings, file, indent = 0, bFowardDeclare = False):
	if IsInListPure(InType, ExportedTypes):
		return
	ExportedTypes.append(InType)
	if isinstance(InType, binaryninja.types.Type):
		#print("Export: '" + str(InType) + "' (type: '" + str(type(InType)) + "'", end="")
		#print(", struct: "+str(InType.structure)+", enum: "+str(InType.enumeration)+", type_class: "+str(InType.type_class)+", named_type_reference: "+str(InType.named_type_reference), end ="")
		#if InType.named_type_reference != None:
		#	print(", named_type_reference.type_class: "+str(InType.named_type_reference.type_class), end ="")
		#	print(", named_type_reference.name: "+str(InType.named_type_reference.name), end ="")
		#	print(", named_type_reference.type_id: "+str(InType.named_type_reference.type_id), end ="")
		#print(")")
		# Struct data
		if InType.structure != None:
			TypeStr = str(InType)
			TypeStr = re.sub(r'<unnamed-type-(\w*)>', r'unnamed_type_\1', TypeStr)
			TypeStrNoPrefix = TypeStr.replace("class ", "").replace("struct ", "").replace("union ", "")
			# Check if we should export this struct/class
			TypePrefixToIgnore = ["class CStlVector<", "class EE::StringBase<", "class EE::String", "struct D3D11", "struct ID3D11", "struct IUnknown", "struct EE::OptListNode<", "class FkStlVector<", "class FkStlList<", "class tiMatrix", "struct CONTAINER<" ]
			TypeContainToIgnore = ["::<lambda_"]
			for TypeToIgnore in TypePrefixToIgnore:
				if TypeStr.startswith(TypeToIgnore):
					#print("THIS SHOULD NO LONGER BE NECESSARY!!")
					return
			for TypeToIgnore in TypeContainToIgnore:
				if TypeToIgnore in TypeStr:
					#print("THIS SHOULD NO LONGER BE NECESSARY!!")
					return
			if bFowardDeclare and not str(InType).startswith("class ") and not str(InType).startswith("struct "):
				return
			# Don't export default library types
			if TypeStrNoPrefix.startswith("std::"):
				return
			# Template
			TemplateMatch = re.match("^(class|struct)(.*)<(.*)>$", TypeStr)
			TemplateTypesStr = None
			if TemplateMatch:
				TemplateTypesStr = TemplateMatch[3].split(",")
				TemplateNameStr = TemplateMatch[2]
				TypeStr = TemplateMatch[1] + TemplateNameStr
				# If template is already declared
				if not "ExportedTemplates" in SessionData:
					SessionData["ExportedTemplates"] = []
				if TemplateNameStr in SessionData["ExportedTemplates"]:
					#print("[Template] '" + TemplateNameStr + "' already exported.")
					return
				SessionData["ExportedTemplates"].append(TemplateNameStr)
			# Find super class
			SuperClassType = None
			if len(InType.structure.members) > 0:
				FirstMember = InType.structure.members[0]
				if (str(FirstMember.name) == "field_0" or str(FirstMember.name) == "Super") and not "*" in str(FirstMember.type) and ("class " in str(FirstMember.type) or "struct " in str(FirstMember.type)):
					SuperClassType = FirstMember.type
			CustomNameSpace = None
			ParentNameSpace = GetParentNameSpaceFromType(InType)
			if ParentNameSpace != None:
				# HACK: Indent check is a hack to ensure we're the root
				if not HasValidParentNameSpace(InType) and indent == 0:
					CustomNameSpace = ParentNameSpace
				TypeStr = TypeStr.replace(ParentNameSpace+"::", "")
			# Raw
			if not bFowardDeclare:
				print("	"*indent + "// [Structure] " + str(InType), file=file)
			# DEBUG: print dependencies
			#if not bFowardDeclare:
			#	DebugPrintDependencies(InType, AllTypes, "	"*indent + "// ", file)
			# Custom NameSpace
			if CustomNameSpace != None:
				print("	"*indent + "namespace " + CustomNameSpace, file=file)
				print("	"*indent + "{", file=file)
				indent = indent + 1
			# Template
			if TemplateMatch:
				print("	"*indent + "template<", end="", file=file)
				i = 1
				for TemplateTypeStr in TemplateTypesStr:
					TemplateNameStr = "T"
					if len(TemplateTypesStr) > 1:
						TemplateNameStr = "T" + str(i)
					if i > 1:
						print(", ", end="", file=file)
					if TemplateTypeStr.isnumeric():
						print("int "+TemplateNameStr, end="", file=file)
					else:
						print("typename "+TemplateNameStr, end="", file=file)
					i = i + 1
				print(">", file=file)
			# Comment
			if not bFowardDeclare and "json" in SessionData and "Comments" in SessionData["json"] and TypeStr in SessionData["json"]["Comments"]:
				print("	"*indent + "/// <summary>", file=file)
				print("	"*indent + "/// " + SessionData["json"]["Comments"][TypeStr], file=file)
				print("	"*indent + "/// </summary>", file=file)
			# Structure name
			print("	"*indent + TypeStr, end="", file=file)
			if SuperClassType != None and not bFowardDeclare:
				print(" : public " + str(SuperClassType).replace("class ", "").replace("struct ", ""), end="", file=file)
			if bFowardDeclare:
				print(";", end="", file=file)
			print("", file=file)
			if not bFowardDeclare:
				print("	"*indent + "{", file=file)
				print("	"*indent + "public:", file=file)
				if file != None:
					file.flush()
				indent = indent+1
				# Export all types in our namespace
				#TypesInNameSpace = GetTypesInNameSpace(InType, AllTypes)
				TypesInNameSpace = InType.calc_typesinnamespace
				if len(TypesInNameSpace) > 0:
					#print("	"*indent + "/// "+str(len(TypesInNameSpace))+" namespace types: ", end="", file=file)
					for TypeIt in TypesInNameSpace:
						ExportType(TypeIt, AllTypes, ExportedTypes, SessionData, ExportedLuaBindings, file, indent)
					#print("", file=file)
				#else:
				#	print("	"*indent + "/// No namespace types", file=file)
				# Export member variables
				print("	"*indent + "/// Struct member variables", file=file)
				print("", file=file)
				FlattenMembers = GetFlattenedStructMembers(InType, None)
				for i in range(0, len(FlattenMembers)):
					MemberIt = FlattenMembers[i]
					# Fill data
					PrevOffset = 0
					if i > 0:
						PrevOffset = FlattenMembers[i-1].offset + FlattenMembers[i-1].type.width
					ExportFiller(InType, SessionData, indent, PrevOffset, MemberIt.offset, file)
					print("	"*indent + "// " + str(MemberIt), file=file)
					MemberName = str(MemberIt.name)
					MemberType = MemberIt.type
					print("	"*indent, end="", file=file)
					# super class member variable
					if SuperClassType != None and MemberIt == InType.structure.members[0]:
						print("// ", end="", file=file)
						MemberName = "Super"
					MemberTypeStr = MemberType.get_string_before_name()
					AfterNameStr = MemberType.get_string_after_name()
					if AfterNameStr.startswith("[") and AfterNameStr.endswith("]"):
						AfterNameStr = AfterNameStr[1:-1]
						# Multiple-dimension arrays
						Split = AfterNameStr.split("][")
						AfterNameStr = "["
						IsFirst = True
						for SplitIt in Split:
							if IsFirst:
								IsFirst = False
							else:
								AfterNameStr = AfterNameStr + "]["
							if "x" in SplitIt:
								AfterNameStr = AfterNameStr + str(int(SplitIt, 16))
							else:
								AfterNameStr = AfterNameStr + SplitIt
						AfterNameStr = AfterNameStr + "]"
					MemberTypeStr = MemberTypeStr.replace("CStlVector<", "std::vector<")
					# If type is literally just enum and nothing else, make it a uint32_t
					if MemberTypeStr == "enum":
						MemberTypeStr = "uint32_t"
					# Const member variables not allowed, so remove const
					if MemberTypeStr.endswith(" const"):
						MemberTypeStr = MemberTypeStr[:-6]
					AfterNameStr = AfterNameStr.replace("* const this", "* const ThisPtr")
					if ParentNameSpace != None:
						MemberTypeStr = MemberTypeStr.replace(ParentNameSpace+"::", "")
					MemberTypeStr = re.sub(r'<unnamed-type-(\w*)>', r'unnamed_type_\1', MemberTypeStr)
					# Replace templates
					if TemplateTypesStr != None:
						i = 1
						for TemplateTypeStrIt in TemplateTypesStr:
							TemplateNameStr = "T"
							if len(TemplateTypesStr) > 1:
								TemplateNameStr = "T"+str(i)
							if TemplateTypeStrIt.isnumeric():
								AfterNameStr = AfterNameStr.replace("[" + TemplateTypeStrIt + "]", "[" + TemplateNameStr + "]")
							else:
								MemberTypeStr = MemberTypeStr.replace("class " + TemplateTypeStrIt, TemplateNameStr)
								MemberTypeStr = MemberTypeStr.replace("struct " + TemplateTypeStrIt, TemplateNameStr)
								MemberTypeStr = MemberTypeStr.replace(TemplateTypeStrIt, TemplateNameStr)
							i = i + 1
					# Default value if possible
					if AfterNameStr == "":
						if MemberTypeStr.endswith("*"):
							AfterNameStr = " = nullptr"
						elif MemberTypeStr == "int16_t" or MemberTypeStr == "uint16_t" or MemberTypeStr == "int32_t" or MemberTypeStr == "uint32_t" or MemberTypeStr == "int8_t" or MemberTypeStr == "uint8_t" or MemberTypeStr == "float" or MemberTypeStr == "double":
							AfterNameStr = " = 0"
					# Hack
					if (MemberTypeStr + "*") in str(MemberType):
						MemberTypeStr = MemberTypeStr + "*"
					print(MemberTypeStr + " " + MemberName + AfterNameStr + ";", file=file)
					print("", file=file)
				# Fill end of type with empty data if nothing to export but size expected
				MemberWidth = 0
				if len(InType.structure.members) > 0:
					MemberWidth = InType.structure.members[-1].offset + InType.structure.members[-1].type.width
				if MemberWidth < InType.width and not (InType.width <= 1 and MemberWidth <= 0):
					ExportFiller(InType, SessionData, indent, MemberWidth, InType.width, file)
				# Functions
				print("	"*indent + "/// "+str(len(InType.calc_functionsinnamespace))+" Functions", file=file)
				print("", file=file)
				if len(InType.calc_functionsinnamespace) > 0:
					for TypeIt in InType.calc_functionsinnamespace:
						ExportType(TypeIt, AllTypes, ExportedTypes, SessionData, ExportedLuaBindings, file, indent)
				# Allow json to extend
				print("	"*indent + "/// Meta", file=file)
				print("", file=file)
				if "json" in SessionData and "Extend" in SessionData["json"] and TypeStr in SessionData["json"]["Extend"] and "Structure" in SessionData["json"]["Extend"][TypeStr]:
					for Entry in SessionData["json"]["Extend"][TypeStr]["Structure"]:
						print("	"*indent + Entry, file=file)
				# Lua meta functions
				HasLuaMetaFunctions = True
				print("	"*indent + "std::string ToString() const", end="", file=file)
				print(" { ", end = "", file=file)
				if "json" in SessionData and "Extend" in SessionData["json"] and TypeStr in SessionData["json"]["Extend"] and "ToString" in SessionData["json"]["Extend"][TypeStr]:
					print(SessionData["json"]["Extend"][TypeStr]["ToString"], end="", file=file)
				else:
					print("std::stringstream stream; stream << \""+TypeStr + " [0x\" << std::hex << GetPtrAddr() << \"]\"; return stream.str();", end="", file=file)
				print(" }", file=file)
				# HACK
				print("	"*indent + "int GetPtrAddr() const", end="", file=file)
				print(" { return (int)this; }", file=file)
				# Copy function
				print("	"*indent + "void CopyFrom("+TypeStrNoPrefix+"& InObject)", file=file)
				print("	"*indent + "{", file=file)
				indent = indent+1
				for MemberIt in GetFlattenedStructMembers(InType, SuperClassType):
					if str(MemberIt.type.get_string_after_name()) == "":
						print("	"*indent + str(MemberIt.name) + " = InObject."+str(MemberIt.name) + ";", file=file)
				indent = indent-1
				print("	"*indent + "}", file=file)
				
				# Expose to Lua (templates not yet supported)
				if TemplateTypesStr == None:
					ExportedLuaBindings.append(InType)
					print("#ifdef WITH_LUA", file=file)
					print("	"*indent + "static void BindLua(luabridge::Namespace& NS)", file=file)
					print("	"*indent + "{", file=file)
					indent = indent+1
					# Class
					TempClassNameC = TypeStrNoPrefix
					TempClassNameLua = TypeStrNoPrefix
					SuperClassName = None
					if SuperClassType != None:
						SuperClassName = str(SuperClassType)
					# Replace templates
					if TemplateTypesStr != None:
						i = 1
						for TemplateTypeStrIt in TemplateTypesStr:
							TemplateNameStr = "T"
							if len(TemplateTypesStr) > 1:
								TemplateNameStr = "T"+str(i)
							TemplateNameLua = "\""+TemplateNameStr+"\""
							TempClassNameC = TempClassNameC.replace("class " + TemplateTypeStrIt, TemplateNameStr)
							TempClassNameC = TempClassNameC.replace("struct " + TemplateTypeStrIt, TemplateNameStr)
							TempClassNameC = TempClassNameC.replace(TemplateTypeStrIt, TemplateNameStr)
							TempClassNameLua = TempClassNameLua.replace("class " + TemplateTypeStrIt, TemplateNameLua)
							TempClassNameLua = TempClassNameLua.replace("struct " + TemplateTypeStrIt, TemplateNameLua)
							TempClassNameLua = TempClassNameLua.replace(TemplateTypeStrIt, TemplateNameLua)
							if SuperClassName != None:
								SuperClassName = SuperClassName.replace("class " + TemplateTypeStrIt, TemplateNameStr)
								SuperClassName = SuperClassName.replace("struct " + TemplateTypeStrIt, TemplateNameStr)
								SuperClassName = SuperClassName.replace(TemplateTypeStrIt, TemplateNameStr)
							i = i + 1
					# Sanitize name
					TempClassNameLua = TempClassNameLua.replace("<", "_").replace(">", "").replace("::", "_").replace(":", "")
					# Templates not yet supported
					if SuperClassType != None and not "<" in str(SuperClassType):
						print("	"*indent + "NS = NS.deriveClass<"+TempClassNameC+", "+SuperClassName.replace("struct ", "").replace("class ", "")+">(\""+TempClassNameLua+"\")", end="", file=file)
					else:
						print("	"*indent + "NS = NS.beginClass<"+TempClassNameC+">(\""+TempClassNameLua+"\")", end="", file=file)
					indent = indent+1
					#ToString
					if HasLuaMetaFunctions:
						print("", file=file)
						print("	"*indent + ".addFunction(\"__tostring\", &"+TypeStrNoPrefix+"::ToString)", file=file)
						print("	"*indent + ".addFunction(\"GetPtrAddr\", &"+TypeStrNoPrefix+"::GetPtrAddr)", end="", file=file)
					# Members
					for MemberIt in GetFlattenedStructMembers(InType, SuperClassType):
						NotSupportedReason = None
						MemberTypeStr = str(MemberIt.type)
						MemberStringAfterName = MemberIt.type.get_string_after_name()
						if MemberTypeStr.startswith("void"):
							NotSupportedReason = "void type not supported in LuaBridge"
						if MemberTypeStr == "char*":
							NotSupportedReason = "char* type not supported in LuaBridge"
						if MemberTypeStr in ["unsigned char*", "int*", "unsigned int*", "short*", "unsigned short*", "__int64*", "int64_t*", "uint64_t*", "int8_t*", "uint8_t*", "int16_t*", "uint16_t*", "int32_t*", "uint32_t*", "float*"]:
							NotSupportedReason = "native pointer type ("+MemberTypeStr+") not supported in LuaBridge (needs wrapper function)"
						if "**" in str(MemberIt.type):
							NotSupportedReason = "pointer to pointer is not supported in LuaBridge"
						if MemberStringAfterName.startswith("[") and MemberStringAfterName.endswith("]"):
							NotSupportedReason = "static arrays are not supported in LuaBridge (only std::vector)"
						if MemberStringAfterName.startswith(")"):
							NotSupportedReason = "delegates are not supported in LuaBridge"
						if MemberTypeStr.endswith(" const"):
							NotSupportedReason = "const not supported in LuaBridge and needs a getter"
						if MemberTypeStr.endswith(" const*"):
							NotSupportedReason = "pointer to const not supported in LuaBridge and needs a getter"
						if MemberTypeStr.endswith(" volatile"):
							NotSupportedReason = "volatile not supported in LuaBridge and needs a getter"
						print("", file=file)
						print("	"*indent, end="", file=file)
						if NotSupportedReason != None:
							print("// " + NotSupportedReason, file=file)
							print("	"*indent, end="", file=file)
							print("//", end="", file=file)
						print(".addProperty(\"" + str(MemberIt.name) + "\", &"+TypeStrNoPrefix+"::"+str(MemberIt.name), end="", file=file)
						# Mark as read-only
						print(")", end="", file=file)
					print("", file=file)
					# Functions
					ExportedFunctions = {}
					for TypeIt in InType.calc_functionsinnamespace:
						FunctionName = GetFunctionNameWithoutNameSpace(TypeIt)
						#print("	"*indent, end="", file=file)
						HasError = None
						if FunctionName in ExportedFunctions:
							ExportedFunctions[FunctionName] = ExportedFunctions[FunctionName] + 1
							FunctionName = FunctionName + "_" + str(ExportedFunctions[FunctionName])
						else:
							ExportedFunctions[FunctionName] = 1
						if HasError == None and len(TypeIt.parameter_vars) > 11:
							HasError = "Can't export functions with more than 11 parameters to LuaBridge."
						if HasError == None:
							for VarIt in TypeIt.parameter_vars:
								VarTypeStr = str(VarIt.type)
								HasError = CanTypeExportInFunction(VarIt.type)
								if HasError != None:
									break
						if HasError != None:
							print("	"*indent + "// "+HasError, file=file)
							print("	"*indent + "//", end="", file=file)
						else:
							print("	"*indent, end="", file=file)
						if FunctionIsStatic(TypeIt):
							print(".addStaticFunction", end="", file=file)
						else:
							print(".addFunction", end="", file=file)
						print("(\"" + str(FunctionName) + "\", &"+TypeStrNoPrefix+"::"+str(FunctionName) + ")", file=file)
					# Json
					if "json" in SessionData and "Extend" in SessionData["json"] and TypeStr in SessionData["json"]["Extend"] and "LuaBindings" in SessionData["json"]["Extend"][TypeStr]:
						for Entry in SessionData["json"]["Extend"][TypeStr]["LuaBindings"]:
							print("	"*indent + Entry, file=file)
					# Lua end func
					indent = indent-1
					print("	"*indent + ".endClass();", file=file)
					indent = indent-1
					print("	"*indent + "}", file=file)
					print("#endif", file=file)
				else:
					print("	"*indent + "// Exporting templated types to Lua currently not supported.", file=file)
					print("	"*indent + "// static void BindLua(luabridge::Namespace& NS)", file=file)
				# Class end
				indent = indent-1
				print("	"*indent + "};", file=file)
			if CustomNameSpace != None:
				indent = indent - 1
				print("	"*indent + "}", file=file)
			if not bFowardDeclare:
				# Static error checking - members
				for MemberIt in GetFlattenedStructMembers(InType, SuperClassType):
					print("	"*indent + "static_assert(sizeof("+TypeStrNoPrefix + "::" + str(MemberIt.name) +") == "+str(MemberIt.type.width)+", \"expected "+TypeStrNoPrefix + "::" + str(MemberIt.name) + " to be size " + str(MemberIt.type.width) + "\");", file=file)
				# Static error checking - class
				print("	"*indent + "static_assert(sizeof("+str(TypeStrNoPrefix)+") == "+str(InType.width)+", \"expected "+TypeStrNoPrefix + " to be size " + str(InType.width) + "\");", file=file)
				print("", file=file)
		# Enum data
		if InType.enumeration != None and not bFowardDeclare:
			TypeStr = str(InType)
			TypePrefixToIgnore = ["enum EE::StringBase<" ]
			for TypeToIgnore in TypePrefixToIgnore:
				if TypeStr.startswith(TypeToIgnore):
					#print("THIS SHOULD NO LONGER BE NECESSARY!!")
					return
			# Find namespace
			CustomNameSpace = None
			ParentNameSpace = GetParentNameSpaceFromType(InType)
			if ParentNameSpace != None:
				# HACK: Indent check is a hack to ensure we're the root
				if not HasValidParentNameSpace(InType) and indent == 0:
					CustomNameSpace = ParentNameSpace
				TypeStr = TypeStr.replace(ParentNameSpace+"::", "")
			print("	"*indent + "// " + str(InType), file=file)
			# Custom NameSpace
			if CustomNameSpace != None:
				print("	"*indent + "namespace " + CustomNameSpace, file=file)
				print("	"*indent + "{", file=file)
				indent = indent + 1
			# Comment
			if not bFowardDeclare and "json" in SessionData and "Comments" in SessionData["json"] and TypeStr in SessionData["json"]["Comments"]:
				print("	"*indent + "/// <summary>", file=file)
				print("	"*indent + "/// " + SessionData["json"]["Comments"][TypeStr], file=file)
				print("	"*indent + "/// </summary>", file=file)
			print("	"*indent + TypeStr + " : uint32_t", file=file)
			print("	"*indent + "{", file=file)
			indent = indent+1
			# Export enum values
			#print("	"*indent + "// Enum values", file=file)
			#print("", file=file)
			IsFirst = True
			for MemberIt in InType.enumeration.members:
				if IsFirst == True:
					IsFirst = False
				else:
					print(",", file=file)
					print("", file=file)
				print("	"*indent + "// " + str(MemberIt), file=file)
				print("	"*indent + str(MemberIt.name) + " = ", end="", file=file)
				# If UINT32_MAX, replace
				if str(MemberIt.value) == "18446744073709551615":
					print("UINT32_MAX", end="", file=file)
				else:
					print(str(MemberIt.value), end="", file=file)
			if IsFirst == False:
				print("", file=file)
			print("", file=file)
			indent = indent-1
			print("	"*indent + "};", file=file)
			if CustomNameSpace != None:
				indent = indent - 1
				print("	"*indent + "}", file=file)
			print("", file=file)
	elif isinstance(InType, binaryninja.function.Function):
		if bFowardDeclare:
			return
		# Operator functions not supported
		if "`" in str(InType) or "::operator" in InType.name:
			print("	"*indent + "// Unsupported operator", file=file)
			print("	"*indent + "//" + str(InType), file=file)
			return
		# Constructor functions not supported
		if InType.name.startswith("??0"):
			print("	"*indent + "// Unsupported constructor", file=file)
			print("	"*indent + "//" + str(InType), file=file)
			return
		# Destructor functions not supported
		if InType.name.startswith("??1"):
			print("	"*indent + "// Unsupported destructor", file=file)
			print("	"*indent + "//" + str(InType), file=file)
			return
		# Not supported
		if InType.name.startswith("??$"):
			print("	"*indent + "// Unsupported function", file=file)
			print("	"*indent + "//" + str(InType), file=file)
			return
		if not "ExportedFunctions" in SessionData:
			SessionData["ExportedFunctions"] = {}
		# Lua bridge does not support function overloading
		ParentNameSpaceStr = GetParentNameSpaceFromType(InType)
		FunctionName = GetFunctionNameWithoutNameSpace(InType)
		FunctionNameWithNameSpace = FunctionName
		# Don't export standard library
		if FunctionNameWithNameSpace.startswith("std::") or (ParentNameSpaceStr != None and ParentNameSpaceStr.startswith("std")):
			print("	"*indent + "// Can't export standard library", file=file)
			print("	"*indent + "//" + str(InType), file=file)
			return
		if ParentNameSpaceStr != None:
			FunctionNameWithNameSpace = ParentNameSpaceStr + "::" + FunctionName
		if FunctionNameWithNameSpace in SessionData["ExportedFunctions"]:
			SessionData["ExportedFunctions"][FunctionNameWithNameSpace] = SessionData["ExportedFunctions"][FunctionNameWithNameSpace] + 1
			FunctionName = FunctionName + "_" + str(SessionData["ExportedFunctions"][FunctionNameWithNameSpace])
		else:
			SessionData["ExportedFunctions"][FunctionNameWithNameSpace] = 1
		# What we pass to the game's function call
		Inputs = ""
		# The parameters to this function
		OuterParameters = ""
		# The parameters used in the typedef
		InnerTypeParameters = ""
		# Additional variables (for std::string)
		AdditionalVariables = []
		i = 0
		IsObjectInstance = False
		for VarIt in InType.parameter_vars:
			VariableName = str(VarIt.name)
			VariableTypeStr = str(VarIt.type)
			# Untyped arguments not supported
			if VariableTypeStr == "void":
				return
			# Delegates not supported
			if "(*)" in VariableTypeStr:
				return
			if VariableName == "":
				VariableName = "arg"+str(i+1)
				# TODO: HACK!!!!
				if VariableTypeStr == "" or VariableTypeStr == "None":
					VariableTypeStr = "uint32_t"
			AdjVariableName = VariableName
			if AdjVariableName == "this":
				AdjVariableName = "thisPtr"
			if InnerTypeParameters != "":
				InnerTypeParameters = InnerTypeParameters + ", "
			InnerTypeParameters = InnerTypeParameters + VariableTypeStr + " " + AdjVariableName
			if VariableTypeStr == "char const*":
				AdditionalVariables.append("char const* " + VariableName + "_c_str = " + VariableName + ".c_str();")
				VariableTypeStr = "std::string"
			if VariableTypeStr == "wchar_t const*":
				AdditionalVariables.append("wchar_t const* " + VariableName + "_c_str = " + VariableName + ".c_str();")
				VariableTypeStr = "std::string"
			# Skip if class' "this" pointer
			if ParentNameSpaceStr != None and VariableName == "this" and i == 0:
				IsObjectInstance = True
			else:
				if OuterParameters != "":
					OuterParameters = OuterParameters + ", "
				# Enum to uint32_t due to lack of LuaBridge support
				if VariableTypeStr.startswith("enum "):
					OuterParameters = OuterParameters + "/* "+VariableTypeStr+" */ uint32_t " + AdjVariableName
				else:
					OuterParameters = OuterParameters + VariableTypeStr + " " + AdjVariableName
			if Inputs != "":
				Inputs = Inputs + ", "
			if VariableTypeStr.startswith("enum "):
				Inputs = Inputs + "(" + VariableTypeStr + ")"
			if IsObjectInstance:
				Inputs = Inputs + VariableName
			else:
				Inputs = Inputs + AdjVariableName
			if VariableTypeStr == "std::string":
				Inputs = Inputs + "_c_str"
			i = i + 1
		# Raw data as comment
		print("	"*indent +"// [Function] " + str(InType) + " [" + str(InType.name) + "]", file=file)
		# DEBUG: print dependencies
		#if not bFowardDeclare:
		#	DebugPrintDependencies(InType, AllTypes, "	"*indent + "// ", file)
		# Comment
		if not bFowardDeclare and "json" in SessionData and "Comments" in SessionData["json"] and str(InType.name) in SessionData["json"]["Comments"]:
			print("	"*indent + "/// <summary>", file=file)
			print("	"*indent + "/// " + SessionData["json"]["Comments"][str(InType.name)], file=file)
			print("	"*indent + "/// </summary>", file=file)
		# Function
		ReturnTypeStr = str(InType.return_type)
		ReturnTypeExportError = None
		if InType.return_type != None:
			ReturnTypeExportError = CanTypeExportInFunction(InType.return_type)
			if ReturnTypeExportError != None:
				print("	"*indent + "// " + ReturnTypeExportError, file=file)
				ReturnTypeStr = "void"
		print("	"*indent, end="", file=file)
		if ParentNameSpaceStr != None and not IsObjectInstance:
			print("static ", end="", file=file)
		# Enum to uint32_t due to lack of LuaBridge support
		if ReturnTypeStr.startswith("enum "):
			print("/* "+ReturnTypeStr+" */ uint32_t", end="", file=file)
		elif ReturnTypeStr == "wchar_t const*" or ReturnTypeStr == "char const*":
			print("std::string", end="", file=file)
		else:
			print(ReturnTypeStr, end="", file=file)
		print(" " + FunctionName + "("+OuterParameters+")", end="", file=file)
		if InType.function_type.const:
			print(" const", end="", file=file)
		print("", file=file)
		print("	"*indent +"{", file=file)
		indent = indent + 1
		# AdditionalVariables
		for AdditionalVariable in AdditionalVariables:
			print("	"*indent + AdditionalVariable, file=file)
		CallingConvention = str(InType.calling_convention)
		if CallingConvention == "cdecl":
			CallingConvention = "fastcall"
		print("	"*indent +"typedef " + str(InType.return_type) + "(__"+CallingConvention+"* _Func)" + "(", end="", file=file)
		#if IsConst and IsObjectInstance:
		#	print("const ", end="", file=file)
		print(InnerTypeParameters+");", file=file)
		print("	"*indent +"_Func mFunc = (_Func)(GameModule + " + str(hex(InType.start)) + ");", file=file)
		# std::string
		if ReturnTypeStr == "wchar_t const*":
			print("	"*indent + ReturnTypeStr + " OutResult = mFunc("+Inputs+");", file=file)
			print("	"*indent + "if (OutResult == nullptr) return std::string();", file=file)
			print("	"*indent + "std::wstring result_wstr(OutResult);", file=file)
			print("	"*indent + "std::string result_str(result_wstr.length(), 0);", file=file)
			print("	"*indent + "std::transform(result_wstr.begin(), result_wstr.end(), result_str.begin(), [](wchar_t c) { return (char)c; });", file=file)
			print("	"*indent + "return result_str;", file=file)
		elif ReturnTypeStr == "char const*":
			print("	"*indent + ReturnTypeStr + " OutResult = mFunc("+Inputs+");", file=file)
			print("	"*indent + "if (OutResult == nullptr) return std::string();", file=file)
			print("	"*indent + "std::string result_str(OutResult);", file=file)
			print("	"*indent + "return result_str;", file=file)
		else:
			print("	"*indent, end="", file=file)
			if ReturnTypeExportError == None:
				print("return ", end="", file=file)
			# Enum to uint32_t due to lack of LuaBridge support
			if ReturnTypeStr.startswith("enum "):
				print("(uint32_t)", end="", file=file)
			print("mFunc" + "("+Inputs+");", file=file)
		indent = indent - 1
		print("	"*indent +"}", file=file)
	#else:
	#	print("Unknown type: '" + str(InType) + "' (type: '" + str(type(InType)) + ")")
		
	if file != None:
		file.flush()

def SortTypesByDependency(TypesToSort, AllTypes, JsonData):
	#print("SortTypesByDependency", end="")
	i = 0
	StuckCheck = 0
	while i < len(TypesToSort):
		#print(".", end="")
		TypeToSort = TypesToSort[i]
		# These are the root types that need to be declared ahead of us
		#DependencyTypes = GetDependencies(TypeToSort, AllTypes, JsonData)
		DependencyTypes = TypeToSort.calc_dependencies
		#print("[SORT] Sorting '" + str(TypeToSort) + "' with " + str(len(DependencyTypes)) + " dependencies")
		AnyPushed = None
		for DependencyType in DependencyTypes:
			if DependencyType == TypeToSort:
				continue
			if not DependencyType in TypesToSort:
				#print("[SORT] -- " + str(DependencyType) + " is not in array")
				continue
			TargetToPush = None
			TargetIndex = 0
			for j in range(i+1, len(TypesToSort)):
				if DependencyType == TypesToSort[j]:
					TargetToPush = TypesToSort[j]
					TargetIndex = j
					break
			if TargetToPush == None:
				#print("[SORT] -- " + str(DependencyType) + " is in front of us already.")
				continue
			if AnyPushed == None:
				AnyPushed = TargetToPush
			# Declare em ahead of us
			del TypesToSort[j]
			TypesToSort.insert(i, TargetToPush)
			if StuckCheck > (5000-8):
			#if True:
				print("[SORT] Pushed '" + str(TargetToPush) + "' ahead of '" + str(TypeToSort) + "'")
		# Walk back one entry in the list so that we'll reprocess the current entry again next loop
		if AnyPushed == None:
			i = i + 1
			StuckCheck = 0
		else:
			StuckCheck = StuckCheck + 1
			if StuckCheck > 5000:
				print("[SORT] Recursive loop detected between '" + str(TypeToSort) + "' and '" + str(AnyPushed) + "'")
				print("[SORT] '" + str(TypeToSort) + "' has ", end="")
				DebugPrintDependencies(TypeToSort, AllTypes, "", None, SessionData, DependencyTypes)
				print("[SORT] '" + str(AnyPushed) + "' has ", end="")
				DebugPrintDependencies(AnyPushed, AllTypes, "", None, SessionData)
				i = i + 1
				StuckCheck = 0

def GetDependencies(InType, AllTypes, JsonData):
	#if "EffectCutMark::Create" in str(InType):
	#	print("Dependencies for " + str(InType) + ":")
	InTypeStr = str(InType)
	DependencyTypes = []
	# Fill the visit list with our outer namespaces so they won't be visited
	NameSpaces = GetNameSpacesFromType(InType)
	NameSpaceTypes = []
	if NameSpaces != None:
		for NameSpace in NameSpaces:
			TypeIt = GetTypeByName(NameSpace)
			if TypeIt == None or TypeIt == InType:
				continue
			NameSpaceTypes.append(TypeIt)
			DependencyTypes.append(TypeIt)
	StartLen = len(DependencyTypes)
	# Visit our type
	VisitType(InType, DependencyTypes, True, False)
	# Visit all types in our namespace
	#TypesInNameSpace = GetTypesInNameSpace(InType, AllTypes)
	for TypeIt in InType.calc_typesinnamespace:
		VisitType(TypeIt, DependencyTypes, True, False)
	for TypeIt in InType.calc_functionsinnamespace:
		VisitType(TypeIt, DependencyTypes, True, False)
	# Visit all custom dependencies
	if JsonData != None and "Extend" in JsonData and InTypeStr in JsonData["Extend"] and "Dependencies" in JsonData["Extend"][InTypeStr]:
		for Entry in JsonData["Extend"][InTypeStr]["Dependencies"]:
			EntryAdj = Entry.replace("struct ", "").replace("class ", "")
			TypeIt = GetTypeByName(EntryAdj)
			if TypeIt == None:
				raise ValueError("Unable to find custom definition '" + EntryAdj + "' for '" + InTypeStr + "'")
			VisitType(TypeIt, DependencyTypes, True, False)
	# Trim away added outer namespaces
	DependencyTypes = DependencyTypes[StartLen:]
	# Remove first entry (InType itself)
	if len(DependencyTypes) > 0:
		DependencyTypes = DependencyTypes[1:]
	#Templates
	TemplateTypes = ["class CStlVector<", "struct EE::OptListNode<", "enum EE::StringBase<", "class std::" ]
	FilteredTypes = []
	for TypeIt in DependencyTypes:
		if TypeIt == None:
			continue
		IsTemplatedType = False
		for TemplateType in TemplateTypes:
			if str(TypeIt).startswith(TemplateType):
				IsTemplatedType = True
				break
		if IsTemplatedType:
			continue
		FilteredTypes.append(TypeIt)
	DependencyTypes = FilteredTypes
	return DependencyTypes


def DebugPrintDependencies(InType, AllTypes, prefix, file, SessionData, DependencyTypes = None):
	# DEBUG: print dependencies
	if DependencyTypes == None:
		#DependencyTypes = GetDependencies(InType, AllTypes, SessionData["json"])
		DependencyTypes = InType.calc_dependencies
	if len(DependencyTypes) > 0:
		print(prefix + str(len(DependencyTypes)) + " dependencies: ", end="", file=file)
		if file != None:
			file.flush()
		IsFirst = True
		for DependencyType in DependencyTypes:
			if IsFirst:
				IsFirst = False
			#else:
				#print(", ", end="", file=file)
			print("", file=file)
			print("// ", end="", file=file)
			print(str(DependencyType), end="", file=file)
			print(" [" + str(type(DependencyType)) + "]", end="", file=file)
			if file != None:
				file.flush()
		print("", file=file)
	else:
		print(prefix + "no dependencies", file=file)

# Returns struct members with duplicate offset members removed
def GetFlattenedStructMembers(InType, InSuperClass = None):
	all_offsets = []
	MemberNum = len(InType.structure.members)
	for i in range(0, MemberNum):
		MemberIt = InType.structure.members[i]
		CurOffset = MemberIt.offset
		if CurOffset in all_offsets:
			continue
		all_offsets.append(CurOffset)
	out = []
	occupied_offsets = []
	for i in range(0, len(all_offsets)):
		CurOffset = all_offsets[i]
		if CurOffset in occupied_offsets:
			continue
		occupied_offsets.append(CurOffset)
		# Super class occupies first member variable
		if InSuperClass != None and CurOffset == 0:
			continue
		TargetSize = InType.width - CurOffset
		if i < len(all_offsets)-1:
			TargetSize = all_offsets[i+1] - CurOffset
		# Get all of offset
		MembersInOffset = []
		for MemberIt in InType.structure.members:
			if MemberIt.offset == CurOffset:
				MembersInOffset.append(MemberIt)	
		# See if we have an exact match
		Matches = []
		for MemberIt in MembersInOffset:
			if MemberIt.type.width == TargetSize:
				Matches.append(MemberIt)
		# Second best: Any that does not overflow
		if len(Matches) <= 0:
			for MemberIt in MembersInOffset:
				if MemberIt.type.width < TargetSize:
					Matches.append(MemberIt)
		if len(Matches) > 0:
			out.append(Matches[0])
	return out

# Export
def DoExport(OutPath, JsonData, AllRootTypes, AllRelevantTypes):
	if JsonData == None:
		JsonData = {}
	# Load json comments
	#with open(JsonPath) as JsonFile:
	#	JsonData = json.load(JsonFile)
	
	with open(OutPath, "w") as text_file:
		print("// Exporter by @MekuCube", file=text_file)
		print("", file=text_file)
		print("#pragma once", file=text_file)
		print("", file=text_file)
		ExportedTypes = []
		ExportedLuaBindings = []
		SessionData = {}
		SessionData["json"] = JsonData
		i = 0
		# Forward declare first
		print("Forward Declaration")
		print("/// Forward Declaration", file=text_file)
		print("", file=text_file)
		for TypeIt in AllRootTypes:
			NumExportPre = len(ExportedTypes)
			#print("Forward declare " + str(i) + " / " + str(len(AllRootTypes)) + ": " + str(TypeIt))
			#profiler = cProfile.Profile()
			#profiler.enable()
			ExportType(TypeIt, AllRelevantTypes, ExportedTypes, SessionData, ExportedLuaBindings, text_file, 0, True)
			#profiler.disable()
			#stats = pstats.Stats(profiler).sort_stats('cumtime')
			#stats.print_stats()
			NumExportPost = len(ExportedTypes)
			if NumExportPre == NumExportPost:
				print("Failed to export anything for root '" + str(TypeIt) + "'")
			#else:
			#	print("Exported " + str(len(ExportedTypes)) + " / " + str(len(AllRelevantTypes)))
			i = i + 1
			#text_file.flush()
		ExportedTypes = []
		SessionData = {}
		SessionData["json"] = JsonData
		ExportedLuaBindings = []
		i = 0
		print("Full Declaration")
		print("", file=text_file)
		print("/// Full Declaration", file=text_file)
		print("", file=text_file)
		# Declaration
		for TypeIt in AllRootTypes:
			NumExportPre = len(ExportedTypes)
			#print("Export definition " + str(i) + " / " + str(len(AllRootTypes)) + ": " + str(TypeIt))
			#profiler = cProfile.Profile()
			#profiler.enable()
			ExportType(TypeIt, AllRelevantTypes, ExportedTypes, SessionData, ExportedLuaBindings, text_file, 0, False)
			#profiler.disable()
			#stats = pstats.Stats(profiler).sort_stats('cumtime')
			#stats.print_stats()
			NumExportPost = len(ExportedTypes)
			if NumExportPre == NumExportPost:
				print("Failed to export anything for root '" + str(TypeIt) + "'")
			#else:
				#print("Exported " + str(len(ExportedTypes)) + " / " + str(len(AllRelevantTypes)))
			i = i + 1
		# Bind to Lua
		print("", file=text_file)
		print("#ifdef WITH_LUA", file=text_file)
		print("/// Lua binding", file=text_file)
		print("", file=text_file)
		print("void BindLua_Exported(luabridge::Namespace& NS)", file=text_file)
		print("{", file=text_file)
		for TypeIt in ExportedLuaBindings:
			TypeStr = str(TypeIt)
			TypeStr = re.sub(r'<unnamed-type-(\w*)>', r'unnamed_type_\1', TypeStr)
			if isinstance(TypeIt, binaryninja.types.Type) and TypeIt.type_class == TypeClass.StructureTypeClass:
				print("#ifdef LOG_INIT", file=text_file)
				print("	" + "std::cout << \"Binding '" + TypeStr + "'\" << std::endl;", file=text_file)
				print("#endif", file=text_file)
				print("	" + TypeStr.replace("class ", "").replace("struct ", "").replace("union ", "") + "::BindLua(NS);", file=text_file)
			else:
				print("	" + "// Cannot export", file=text_file)
				print("	" + TypeStr.replace("class ", "").replace("struct ", "").replace("union ", "") + "::BindLua(NS);", file=text_file)
		print("}", file=text_file)
		print("#endif", file=text_file)
				
		for TypeIt in AllRelevantTypes:
			if not TypeIt in ExportedTypes:
				print("Failed to export: '" + str(TypeIt) + "'")


#def UpdateReferences(InType, AllTypes, JsonData):
#	setattr(InType, 'calc_typesinnamespace', GetTypesInNameSpace(InType, AllTypes))
#	setattr(InType, 'calc_dependencies', GetDependencies(InType, AllTypes, JsonData))

# Check that json is valid before we begin
JsonData = None
with open("E:/C++/NoMoreHeroesModLua/Games/gamecomments.json") as JsonFile:
	JsonData = json.load(JsonFile)

AllRelevantTypes = []
#CollectTypes(AllRelevantTypes, ["GdlSentence"])
CollectTypes(AllRelevantTypes, ["mHRChara", "mHRBattle", "mHRPc", "HrMap", "mHRPad", "HrMessage", "HrSysMessage", "HrScreenStatus", "HrMissionResult", "HrTalk", "GdlLines", "WGdl", "GdlHeader", "GdlDialog", "GdlSentence", "MessLines", "CBgCtrl", "HrStageDraw", "rSkyMap", "rSkyMapMenu"])
print("Collected " + str(len(AllRelevantTypes)) + " types.")

# Only export roots
AllRootTypes = []
AllNonRootTypes = []
for TypeIt in AllRelevantTypes:
	# Has a parent
	if HasValidParentNameSpace(TypeIt):
		AllNonRootTypes.append(TypeIt)
		continue
	if isinstance(TypeIt, binaryninja.types.Type):
		if TypeIt.type_class != TypeClass.StructureTypeClass and TypeIt.type_class != TypeClass.EnumerationTypeClass:
			AllNonRootTypes.append(TypeIt)
			continue
	#print("[Root] " + str(TypeIt) + " is root")
	AllRootTypes.append(TypeIt)

print("Calculating parent namespaces.")
i = 0
for TypeIt in AllRelevantTypes:
	i = i + 1
	#if i % 50 == 0:
	#	print("[" + str(i) + " / " + str(len(AllRelevantTypes)) + "] " + str(TypeIt))
	# Parent namespace type
	ParentNameSpaceStr = GetParentNameSpaceFromType(TypeIt);
	if "GetCharaNowPlayMotionTick" in str(TypeIt):
		print("Parent namespace for '" + str(TypeIt) + "': '" + str(ParentNameSpaceStr) + "'")
	if ParentNameSpaceStr == None:
		setattr(TypeIt, 'calc_parentnamespace_str', None)
		setattr(TypeIt, 'calc_parentnamespace_type', None)
	else:
		setattr(TypeIt, 'calc_parentnamespace_str', ParentNameSpaceStr)
		setattr(TypeIt, 'calc_parentnamespace_type', GetTypeByName(ParentNameSpaceStr))

print("Calculating types in namespace.")
i = 0
for TypeIt in AllRelevantTypes:
	i = i + 1
	#if i % 200 == 0:
	#	print("[" + str(i) + " / " + str(len(AllRelevantTypes)) + "] " + str(TypeIt))
	# Types in namespace
	TypesInNameSpace = GetTypesInNameSpace(TypeIt, AllNonRootTypes);
	FunctionsInNameSpace = []
	NonFunctionsInNameSpace = []
	for TypeIt2 in TypesInNameSpace:
		if isinstance(TypeIt2, binaryninja.function.Function):
			FunctionsInNameSpace.append(TypeIt2)
		else:
			NonFunctionsInNameSpace.append(TypeIt2)
	setattr(TypeIt, 'calc_typesinnamespace', NonFunctionsInNameSpace)
	setattr(TypeIt, 'calc_functionsinnamespace', FunctionsInNameSpace)

print("Calculating dependencies.")
i = 0
for TypeIt in AllRelevantTypes:
	i = i + 1
	#if i % 200 == 0:
	#	print("[" + str(i) + " / " + str(len(AllRelevantTypes)) + "] " + str(TypeIt))
	#p = multiprocessing.Process(target = UpdateReferences, args=(TypeIt, AllRelevantTypes, JsonData))
	#p.start()
	#AllThreads.append(p)
	
	#multiprocessing.apply(UpdateReferences, args=(TypeIt, AllRelevantTypes, JsonData))
	
	#with PoolExecutor() as executor:
	#	for timing, result in executor.map(UpdateReferences, (TypeIt, AllRelevantTypes, JsonData)):
	#		# put results into correct output list:
	#		timings.append(timing), results.append(result)
	#UpdateReferences(TypeIt, AllRelevantTypes, JsonData)
	setattr(TypeIt, 'calc_dependencies', GetDependencies(TypeIt, AllRelevantTypes, JsonData))

print("Sorting types in namespace.")
i = 0
for TypeIt in AllRelevantTypes:
	i = i + 1
	#if i % 200 == 0:
	#	print("[" + str(i) + " / " + str(len(AllRelevantTypes)) + "] " + str(TypeIt))
	 # Sort em
	SortTypesByDependency(TypeIt.calc_typesinnamespace, AllRelevantTypes, JsonData)
	setattr(TypeIt, 'calc_typesinnamespace', TypeIt.calc_typesinnamespace)

#for ThreadIt in AllThreads:
#	ThreadIt.join()
#profiler = cProfile.Profile()
#profiler.enable()
print("Sorting types.")
SortTypesByDependency(AllRootTypes, AllRelevantTypes, JsonData)
#profiler.disable()
#stats = pstats.Stats(profiler).sort_stats('cumtime')
#stats.print_stats()
print("Root types: " + str(len(AllRootTypes)))
#for TypeIt in AllRootTypes:
#	print(TypeIt, end=", ")

#print("")

DoExport("E:/C++/NoMoreHeroesModLua/Games/NMH2/exported_data_types.h", JsonData, AllRootTypes, AllRelevantTypes)

print("Complete")