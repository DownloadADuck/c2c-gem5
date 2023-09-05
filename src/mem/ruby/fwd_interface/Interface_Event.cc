#include <cassert>
#include <iostream>
#include <string>

#include "base/logging.hh"
#include "mem/ruby/protocol/Interface_Event.hh"

namespace gem5
{

namespace ruby
{


::std::ostream&
operator<<(::std::ostream& out, const Interface_Event& obj)
{
    out << Interface_Event_to_string(obj);
    out << ::std::flush;
    return out;
}

// Code to convert state to a string
std::string
Interface_Event_to_string(const Interface_Event& obj)
{
    switch(obj) {
      case Interface_Event_request:
        return "request";
      case Interface_Event_snoop:
        return "snoop";
      case Interface_Event_response:
        return "response";
      case Interface_Event_data:
        return "data";
      case Interface_Event_fwd:
        return "fwd";
      default:
        panic("Invalid range for type Interface_Event");
    }
    // Appease the compiler since this function has a return value
    return "";
}

// Code to convert from a string to the enumeration
Interface_Event
string_to_Interface_Event(const std::string& str)
{
    if (str == "request") {
        return Interface_Event_request;
    } else if (str == "snoop") {
        return Interface_Event_snoop;
    } else if (str == "response") {
        return Interface_Event_response;
    } else if (str == "data") {
        return Interface_Event_data;
    } else if (str == "fwd") {
        return Interface_Event_fwd;
    } else {
        panic("Invalid string conversion for %s, type Interface_Event", str);
    }
}

// Code to increment an enumeration type
Interface_Event&
operator++(Interface_Event& e)
{
    assert(e < Interface_Event_NUM);
    return e = Interface_Event(e+1);
}

} // namespace ruby
} // namespace gem5