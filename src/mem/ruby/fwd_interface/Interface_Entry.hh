
#ifndef __Interface_Entry_HH__
#define __Interface_Entry_HH__

#include <iostream>

#include "mem/ruby/slicc_interface/RubySlicc_Util.hh"

#include "mem/ruby/protocol/Interface_State.hh"
#include "mem/ruby/protocol/NetDest.hh"
#include "mem/ruby/protocol/AbstractCacheEntry.hh"

namespace gem5
{

namespace ruby
{

class Interface_Entry :  public AbstractCacheEntry
{
  public:
    Interface_Entry
()
		{
        m_InterfaceState = Interface_State_IDLE;
         // default value of Interface_State
        // m_Sharers has no default
        // m_Owner has no default
    }
    Interface_Entry(const Interface_Entry&) = default;
    Interface_Entry
    &operator=(const Interface_Entry&) = default;
    Interface_Entry(const Interface_State& local_InterfaceState, const NetDest& local_Sharers, const NetDest& local_Owner)
        : AbstractCacheEntry()
    {
        m_InterfaceState = local_InterfaceState;
        m_Sharers = local_Sharers;
        m_Owner = local_Owner;
    }
    Interface_Entry*
    clone() const
    {
         return new Interface_Entry(*this);
    }
    // Const accessors methods for each field
    /** \brief Const accessor method for InterfaceState field.
     *  \return InterfaceState field
     */
    const Interface_State&
    getInterfaceState() const
    {
        return m_InterfaceState;
    }
    /** \brief Const accessor method for Sharers field.
     *  \return Sharers field
     */
    const NetDest&
    getSharers() const
    {
        return m_Sharers;
    }
    /** \brief Const accessor method for Owner field.
     *  \return Owner field
     */
    const NetDest&
    getOwner() const
    {
        return m_Owner;
    }
    // Non const Accessors methods for each field
    /** \brief Non-const accessor method for InterfaceState field.
     *  \return InterfaceState field
     */
    Interface_State&
    getInterfaceState()
    {
        return m_InterfaceState;
    }
    /** \brief Non-const accessor method for Sharers field.
     *  \return Sharers field
     */
    NetDest&
    getSharers()
    {
        return m_Sharers;
    }
    /** \brief Non-const accessor method for Owner field.
     *  \return Owner field
     */
    NetDest&
    getOwner()
    {
        return m_Owner;
    }
    // Mutator methods for each field
    /** \brief Mutator method for InterfaceState field */
    void
    setInterfaceState(const Interface_State& local_InterfaceState)
    {
        m_InterfaceState = local_InterfaceState;
    }
    /** \brief Mutator method for Sharers field */
    void
    setSharers(const NetDest& local_Sharers)
    {
        m_Sharers = local_Sharers;
    }
    /** \brief Mutator method for Owner field */
    void
    setOwner(const NetDest& local_Owner)
    {
        m_Owner = local_Owner;
    }
    void print(std::ostream& out) const;
  //private:
    /** Directory state */
    Interface_State m_InterfaceState;
    /** Sharers for this block */
    NetDest m_Sharers;
    /** Owner of this block */
    NetDest m_Owner;
};
inline ::std::ostream&
operator<<(::std::ostream& out, const Interface_Entry& obj)
{
    obj.print(out);
    out << ::std::flush;
    return out;
}

} // namespace ruby
} // namespace gem5

#endif // __Interface_Entry_HH__
