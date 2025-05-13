
// void print(std::ostream% out) const;
#include "mem/ruby/common/MegaNetDest.hh"

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

// adding a single NetDest
void
MegaNetDest::add(int chipID, MachineID dest) 
{
    assert(chipID >= 0 && chipID < m_numChips);
    m_data[chipID].add(dest);
}

// merging an entire MegaNetDest
void 
MegaNetDest::addMegaNetDest(int chipID, const MegaNetDest& mega) 
{
    assert(mega.m_numChips == m_numChips);
    m_data[chipID].addNetDest(mega.m_data[chipID]);
}

// removes a single dest
void 
MegaNetDest::remove(int chip, MachineID dest) 
{
    assert(chip >= 0 && chip < m_numChips);
    m_data[chip].remove(dest);
}

// removes a MegaNetDest
void
MegaNetDest::remove(const MegaNetDest& mega)
{
    assert(mega.m_numChips == m_numChips);
    for (int i = 0; i < m_numChips; ++i)
        m_data[i].removeNetDest(mega.m_data[i]);
}

void
MegaNetDest::resize()
{
    m_data.resize(m_numChips);
    for (int i = 0; i < m_numChips; ++i) {
        m_data[i].resize();
    }
}

bool
MegaNetDest::isPresent(MachineID dest) const 
{
    for (int chip = 0; chip < m_numChips; ++chip) {
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
    //for (int i = 0; i < m_bits.size(); i++) {
    //    if (!m_bits[i] != 0) {
    //        return false;
    //    }
    //}
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
    out << "[MegaNetDest with " << m_numChips << " chips]\n";
    for (int i = 0; i < m_numChips; ++i) {
        out << "  Chip " << i << ": " << m_data[i] << "\n";
    }
}

} // namespace ruby
} // namespace gem5