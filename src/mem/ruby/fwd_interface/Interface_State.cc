
#include <cassert>
#include <iostream>
#include <string>

#include "base/logging.hh"
#include "mem/ruby/fwd_interface/Interface_State.hh"

namespace gem5
{

namespace ruby
{

// Code to convert the current state to an access permission
AccessPermission Interface_State_to_permission(const Interface_State& obj)
{
    switch(obj) {
      case Interface_State_IDLE:
        return AccessPermission_Read_Write;
      case Interface_State_FWD:
        return AccessPermission_Busy;
      default:
        panic("Unknown state access permission converstion for Interface_State");
    }
    // Appease the compiler since this function has a return value
    return AccessPermission_Invalid;
}

// Code for output operator
::std::ostream&
operator<<(::std::ostream& out, const Interface_State& obj)
{
    out << Interface_State_to_string(obj);
    out << ::std::flush;
    return out;
}

// Code to convert state to a string
std::string
Interface_State_to_string(const Interface_State& obj)
{
    switch(obj) {
      case Interface_State_IDLE:
        return "IDLE";
      case Interface_State_FWD:
        return "FWD";
      default:
        panic("Invalid range for type Interface_State");
    }
    // Appease the compiler since this function has a return value
    return "";
}

// Code to convert from a string to the enumeration
Interface_State
string_to_Interface_State(const std::string& str)
{
    if (str == "IDLE") {
        return Interface_State_IDLE;
    } else if (str == "FWD") {
        return Interface_State_FWD;
    } else {
        panic("Invalid string conversion for %s, type Interface_State", str);
    }
}

// Code to increment an enumeration type
Interface_State&
operator++(Interface_State& e)
{
    assert(e < Interface_State_NUM);
    return e = Interface_State(e+1);
}
} // namespace ruby
} // namespace gem5
