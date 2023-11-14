#ifndef __Interface_Event_HH__
#define __Interface_Event_HH__

#include <iostream>
#include <string>

namespace gem5
{

namespace ruby
{

// Class definition
/** \enum Interface_Event
 *  \brief Interface events
*/
enum Interface_Event {
    Interface_Event_FIRST,
    Interface_Event_requestToBridge = Interface_Event_FIRST,
    Interface_Event_snoopToBridge,
    Interface_Event_responseToBridge,
    Interface_Event_dataToBridge,
    Interface_Event_requestToNetwork,
    Interface_Event_snoopToNetwork,
    Interface_Event_responseToNetwork,
    Interface_Event_dataToNetwork,
    Interface_Event_fwd,
    Interface_Event_NUM
};

// Code to convert from a string to the enumeration
Interface_Event string_to_Interface_Event(const ::std::string& str);

// Code to convert from a state to a string 
::std::string Interface_Event_to_string(const Interface_Event& obj);

// Code to increment an enumeration type
Interface_Event &operator++(Interface_Event &e);

::std::ostream&
operator<<(::std::ostream& out, const Interface_Event& obj);

} // namespace ruby
} // namespace gem5
#endif // __Interface_Event_HH__