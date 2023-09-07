#ifndef __Interface_State_HH__
#define __Interface_State_HH__

#include <iostream>
#include <string>

#include "mem/ruby/protocol/AccessPermission.hh"
namespace gem5
{

namespace ruby
{


// Class definition
/** \enum Interface_State
 *  \brief Interface states
*/
enum Interface_State {
    Interface_State_FIRST,
    Interface_State_IDLE = Interface_State_FIRST, /**< Idle, waiting a for requests */
    Interface_State_FWD,
    Interface_State_NUM
};

// Code to convert from a string to the enumeration
Interface_State string_to_Interface_State(const ::std::string& str);

// Code to convert state to a string
::std::string Interface_State_to_string(const Interface_State& obj);

// Code to increment an enumeration type
Interface_State &operator++(Interface_State &e);

// Code to convert the current state to an access permission
AccessPermission Interface_State_to_permission(const Interface_State& obj);


::std::ostream&
operator<<(::std::ostream& out, const Interface_State& obj);

} // namespace ruby
} // namespace gem5
#endif // __Interface_State_HH__