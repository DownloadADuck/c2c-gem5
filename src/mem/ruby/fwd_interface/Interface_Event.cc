#include <cassert>
#include <iostream>
#include <string>

#include "base/logging.hh"
#include "mem/ruby/fwd_interface/Interface_Event.hh"

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
      case Interface_Event_requestToBridge:
        return "requestToBridge";
      case Interface_Event_snoopToBridge:
        return "snoopToBridge";
      case Interface_Event_responseToBridge:
        return "responseToBridge";
      case Interface_Event_dataToBridge:
        return "dataToBridge";
      case Interface_Event_requestToNetwork:
        return "requestToNetwork";
      case Interface_Event_snoopToNetwork:
        return "snoopToNetwork";
      case Interface_Event_responseToNetwork:
        return "responseToNetwork";
      case Interface_Event_dataToNetwork:
        return "dataToNetwork";
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
    if (str == "requestToBridge") {
        return Interface_Event_requestToBridge;
    } else if (str == "snooptoBridge") {
        return Interface_Event_snoopToBridge;
    } else if (str == "responseToBridge") {
        return Interface_Event_responseToBridge;
    } else if (str == "dataToBridge") {
        return Interface_Event_dataToBridge;
    } else if (str == "requestToNetwork") {
        return Interface_Event_requestToNetwork;
    } else if (str == "snoopToNetwork") {
        return Interface_Event_snoopToNetwork;
    } else if (str == "responseToNetwork") {
        return Interface_Event_responseToNetwork;
    } else if (str == "dataToNetwork") {
        return Interface_Event_dataToNetwork;
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