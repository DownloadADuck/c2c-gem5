// MegaNetDest
// Vector of NetDest allowing to track off-chip sharers of a
// cache line in multi-chip architecture

#include "mem/ruby/common/MegaNetDest.hh"
#include "mem/ruby/common/NetDest.hh"

#include <iostream>
#include <algorithm>
#include <sstream>

namespace gem5
{

namespace ruby
{

MegaNetDest::MegaNetDest()
{
    resize();
}

// adding a single machine to a NetDest 
void
MegaNetDest::add(MachineID dest, int chipID) 
{
    int numChips = MachineType_base_count(MachineType_Interface);
    assert(chipID >= 0 && chipID < numChips);
    m_data[chipID].add(dest);
}

MegaNetDest
MegaNetDest::addMegaNetDest(MegaNetDest mega)
{
    return mega;
}

// merging an entire MegaNetDest
void 
MegaNetDest::mergeMegaNetDest(int chipID, const MegaNetDest& mega) 
{
    int numChips = MachineType_base_count(MachineType_Interface);
    assert(mega.m_data.size() == numChips);
    m_data[chipID].addNetDest(mega.m_data[chipID]);
}

NetDest
MegaNetDest::extractNetDest(int chipID)
{
    int numChips = MachineType_base_count(MachineType_Interface);
    assert(chipID >= 0 && chipID < numChips);
    return m_data[chipID];
}

// removes a single dest
void 
MegaNetDest::remove(int chip, MachineID dest) 
{
    int numChips = MachineType_base_count(MachineType_Interface);
    assert(chip >= 0 && chip < numChips);
    m_data[chip].remove(dest);
}

// removes a MegaNetDest
void
MegaNetDest::remove(const MegaNetDest& mega)
{
    int numChips = MachineType_base_count(MachineType_Interface);
    assert(mega.m_data.size() == numChips);
    for (int i = 0; i < numChips; ++i)
        m_data[i].removeNetDest(mega.m_data[i]);
}

void
MegaNetDest::resize()
{
    int numChips = MachineType_base_count(MachineType_Interface);
    m_data.resize(numChips);
    for (int i = 0; i < numChips; ++i) {
        m_data[i].resize();
    }
}

MachineID
MegaNetDest::smallestElement() const
{
    assert(totalCount() > 0);
    int numChips = MachineType_base_count(MachineType_Interface);
    for (int i = 0; i < numChips; ++i) {
        if (!m_data[i].isEmpty()) {
            return m_data[i].smallestElement();
        }
    }
    panic("No smallest element of an empty set.");
}

MachineID
MegaNetDest::smallestElement(MachineType machine) const
{
    int numChips = MachineType_base_count(MachineType_Interface);
    for (int i = 0; i < numChips; ++i) {
        if (!m_data[i].isEmpty()) {
            return m_data[i].smallestElement(machine);
        }
    }
    panic("No smallest elemtn of given MachineType.");
}

bool
MegaNetDest::isElement(MachineID dest) const 
{
    int numChips = MachineType_base_count(MachineType_Interface);
    for (int chip = 0; chip < numChips; ++chip) {
        if (m_data[chip].isElement(dest)){
            return true;
        }
    }
    return false;
}

void
MegaNetDest::clear()
{
    for (auto &nd : m_data) nd.clear();
}

int
MegaNetDest::totalCount() const
{
    int sum = 0;
    for (auto &nd : m_data) sum += nd.count();
    return sum;
}

bool
MegaNetDest::isEmpty() const
{
    for (auto &nd : m_data) if (!nd.isEmpty()) return false;
    return true;
}

bool
MegaNetDest::isBroadcast() const
{
    for (auto &nd : m_data) if (!nd.isBroadcast()) return false;
    return true;
}

void
MegaNetDest::print(std::ostream& out) const
{
    int numChips = MachineType_base_count(MachineType_Interface);
    out << "[MegaNetDest with " << numChips << " chips]\n";
    for (int i = 0; i < numChips; ++i) {
        out << "  Chip " << i << ": " << m_data[i] << "\n";
    }
}

} // namespace ruby
} // namespace gem5