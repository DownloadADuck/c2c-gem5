// MegaNetDest
// Vector of NetDest allowing to track off-chip sharers of a
// cache line in multi-chip architecture

#include "mem/ruby/common/MegaNetDest.hh"
#include "mem/ruby/common/NetDest.hh"

#include <iostream>
#include <algorithm>
#include <sstream>
#include <cmath>

namespace gem5
{

namespace ruby
{

MegaNetDest::MegaNetDest()
{
    resize();
}

static int 
numChipsFromInterfaces(int numInterfaces)
{
    return (1 + std::sqrt(1 + 4 * numInterfaces)) / 2;
}

// adding a single machine to a NetDest 
void
MegaNetDest::add(int chipID, MachineID dest) 
{
    int numInterfaces = MachineType_base_count(MachineType_Interface);
    int numChips = numChipsFromInterfaces(numInterfaces);
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
MegaNetDest::mergeMegaNetDest(const MegaNetDest& mega)
{
    // ensure recipient is big enough
    if (m_data.size() < mega.m_data.size()) {
        m_data.resize(mega.m_data.size());
    }
    // merge
    for (size_t i=0; i < mega.m_data.size(); ++i) {
        m_data[i].addNetDest(mega.m_data[i]);
    }
}
void 
MegaNetDest::mergeMegaNetDest(int chipID, const MegaNetDest& mega) 
{
    int numInterfaces = MachineType_base_count(MachineType_Interface);
    int numChips = numChipsFromInterfaces(numInterfaces);
    assert(mega.m_data.size() == numChips);
    m_data[chipID].addNetDest(mega.m_data[chipID]);
}

NetDest
MegaNetDest::extractNetDest(int chipID)
{
    int numInterfaces = MachineType_base_count(MachineType_Interface);
    int numChips = numChipsFromInterfaces(numInterfaces);
    assert(chipID >= 0 && chipID < numChips);
    return m_data[chipID];
}

// removes a single dest
void 
MegaNetDest::remove(int chip, MachineID dest) 
{
    int numInterfaces = MachineType_base_count(MachineType_Interface);
    int numChips = numChipsFromInterfaces(numInterfaces);
    assert(chip >= 0 && chip < numChips);
    m_data[chip].remove(dest);
}

// removes a MegaNetDest
void
MegaNetDest::remove(const MegaNetDest& mega)
{
    int numInterfaces = MachineType_base_count(MachineType_Interface);
    int numChips = numChipsFromInterfaces(numInterfaces);
    assert(mega.m_data.size() == numChips);
    // TODO: Find another way of generating numChips
    for (int i = 0; i < numChips; ++i)
        m_data[i].removeNetDest(mega.m_data[i]);
}

void
MegaNetDest::resize()
{
    int numInterfaces = MachineType_base_count(MachineType_Interface);
    int numChips = numChipsFromInterfaces(numInterfaces);
    m_data.resize(numChips);
    for (int i = 0; i < numChips; ++i) {
        m_data[i].resize();
    }
}

MegaNetDest
MegaNetDest::smallestElement() const
{
    assert(totalCount() > 0);
    int numInterfaces = MachineType_base_count(MachineType_Interface);
    int numChips = numChipsFromInterfaces(numInterfaces);

    for (int i = 0; i < numChips; ++i) {
        if (!m_data[i].isEmpty()) {
            MachineID smallest = m_data[i].smallestElement();

            MegaNetDest result;
            result.m_data.resize(numChips);
            result.m_data[i].add(smallest);

            return result;
        }
    }
    panic("No smallest element of an empty set.");
}

MegaNetDest
MegaNetDest::smallestElement(MachineType machine) const
{
    int numInterfaces = MachineType_base_count(MachineType_Interface);
    int numChips = numChipsFromInterfaces(numInterfaces);

    for (int i = 0; i < numChips; ++i) {
        if (!m_data[i].isEmpty()) {
            int base = MachineType_base_level(machine);
            if (base >= m_data[i].count()) continue;

            MachineID smallest = m_data[i].smallestElement(machine);

            MegaNetDest result;
            result.m_data.resize(numChips);
            result.m_data[i].add(smallest);

            return result;
        }
    }
    panic("No smallest elemtn of given MachineType.");
}

bool
MegaNetDest::isElement(int chipID, MachineID dest) const 
{
    if (m_data[chipID].isElement(dest)){
        return true;
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

int
MegaNetDest::chipCount() const
{
    return m_data.size();
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
    int numInterfaces = MachineType_base_count(MachineType_Interface);
    int numChips = numChipsFromInterfaces(numInterfaces);
    out << "[MegaNetDest with " << numChips << " chips]\n";
    for (int i = 0; i < numChips; ++i) {
        out << "  Chip " << i << ": " << m_data[i] << "\n";
    }
}

} // namespace ruby
} // namespace gem5