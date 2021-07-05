// Common types used by both NMH and NMH2

#pragma once

namespace EE
{
    template<class T>
    struct OptListNode
    {
    public:
        /// No namespace types
        /// Struct member variables

        // <class GXTexture* value, offset 0x0>
        T value;

        // <EE::OptListNode<GXTexture *>* next, offset 0x4>
        EE::OptListNode<T>* next;

        // <EE::OptListNode<GXTexture *>* prev, offset 0x8>
        EE::OptListNode<T>* prev;

    };
}

class tiMatrix
{
	char _Filler[64];
};

template<typename T>
class FkStlVector
{
public:
	// <int32_t m_nCapacity, offset 0x0>
	int32_t m_nCapacity;

	// <int32_t m_nSize, offset 0x4>
	int32_t m_nSize;

	// <T* m_pData, offset 0x8>
	T* m_pData;

	// <char m_DbgName[0x8], offset 0xc>
	char m_DbgName[8];

};

template<typename T>
struct CONTAINER
{
public:
    /// No namespace types
    /// Struct member variables

    // <class commonObj* Val, offset 0x0>
    T Val;

    // <CONTAINER<commonObj *>* pPrev, offset 0x4>
    CONTAINER<T>* pPrev;

    // <CONTAINER<commonObj *>* pNext, offset 0x8>
    CONTAINER<T>* pNext;
};

template<typename T>
class FkStlList
{
public:
    // <struct CONTAINER<commonObj *>* m_pTop, offset 0x0>
    struct CONTAINER<T>* m_pTop;

    // <struct CONTAINER<commonObj *>* m_pEnd, offset 0x4>
    struct CONTAINER<T>* m_pEnd;

    // <int32_t m_nSize, offset 0x8>
    int32_t m_nSize;
};

namespace EE
{
	class StringBase
	{
    public:
        enum Storage : uint32_t
        {
            INTERNAL = 0x0,
            EXTERNAL = 0x1,
            REFCOUNTED = 0x2
        };

		void const* any;
		uint32_t length;
		enum Storage storage;
	};
	class String
	{
    public:
		class StringBase field_0;
	};
}