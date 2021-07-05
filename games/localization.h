// Common types used by both NMH and NMH2

#include <iostream>
#include <set>
#pragma once

#define MIN_DIALOG_EXPANSION_SPACE 1000

GdlDialog* CreateDialogFromString(std::string InString)
{
	// LEAK: this will leak memory and I don't care (yet)

	std::wstring* widestr = new std::wstring(InString.begin(), InString.end());

	GdlDialog* Dialog = new GdlDialog();
	GdlLines* Lines = new GdlLines();

	GdlSentence* Sentence = new GdlSentence();
	Sentence->mpLettersUc = widestr->c_str();

	// Add sentence to line
	Lines->mppSentencePtrTable = new GdlSentence * [] { Sentence };
	Lines->mSentenceCount = 1;

	// Add line to dialog
	Dialog->mppLinesPtrTable = new GdlLines * [] { Lines };
	Dialog->mLinesCount = 1;

	return Dialog;
}

// Return: Dialog index
uint16_t ExpandWGdl(WGdl* InDialog, std::string InString)
{
	static std::set<GdlHeader*> ExpandedHeaders;

	GdlHeader* Header = nullptr;
	auto It = ExpandedHeaders.find(InDialog->mpData);
	if (It == ExpandedHeaders.end())
	{

		Header = new GdlHeader();
		Header->CopyFrom(*InDialog->mpData);
		ExpandedHeaders.insert(Header);

		// Create new header entries (with extra space for our entry)
		Header->mppDialogPtrTable = new GdlDialog*[std::max<uint16_t>(Header->mDialogCount, MIN_DIALOG_EXPANSION_SPACE)]{ 0 };
		// Copy data
		for (uint16_t i = 0; i < Header->mDialogCount; i++)
			Header->mppDialogPtrTable[i] = InDialog->mpData->mppDialogPtrTable[i];

		// Add header to global
		InDialog->mpData = Header;
	}
	else
	{
		Header = *It;
	}

	if (Header == nullptr)
		return 0;

	if (Header->mDialogCount >= MIN_DIALOG_EXPANSION_SPACE - 1)
	{
		// Out of entries
		std::cout << "OUT OF DIALOG ENTRIES" << std::endl;
		return 0;
	}
	Header->mDialogCount++;
	Header->mppDialogPtrTable[Header->mDialogCount-1] = CreateDialogFromString(InString);

	// Return dialog index
	return Header->mDialogCount-1;
}

bool ShowMessage(std::string InMessage, bool bSkipIfExists = false)
{
	std::cout << InMessage << std::endl;
	if (GetHrMessage() != nullptr and GetScreenStatus() != nullptr)
	{
		uint16_t Index = ExpandWGdl(GetHrMessage()->mp_Gdl, InMessage);
		GetScreenStatus()->BattleSimplMessage(Index, bSkipIfExists);
		return true;
	}
	return false;
}