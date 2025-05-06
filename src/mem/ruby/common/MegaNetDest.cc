
// void print(std::ostream% out) const;
#include "mem/ruby/common/MegaNetDest.hh"

#include <iostream>
#include <algorithm>
#include <sstream>

namespace gem5
{

namespace ruby
{

//MegaNetDest::MegaNetDest(int numChips, int nodesPerNet) 
// : m_numChips(numChips) 
//{
//    m_data.reserve(numChips);
//    for (int i = 0; i < numChips; ++i)
//        m_data.emplace_back(nodesPerNet);
//}
MegaNetDest::MegaNetDest()
{
    resize();
}

// adding a single NetDest
void
MegaNetDest::add(int chip, MachineID dest) 
{
    assert(chip >= 0 && chip < m_numChips);
    m_data[chip].add(dest);
}

// merging an entire MegaNetDest
void 
MegaNetDest::add(const MegaNetDest& mega) 
{
    assert(mega.m_numChips == m_numChips);
    for (int i = 0; i < m_numChips; ++i)
        m_data[i].addNetDest(mega.m_data[i]);
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

}

bool
MegaNetDest::isPresent(int chip, MachineID dest) const 
{
    assert(chip >= 0 && chip < m_numChips);
    return m_data[chip].isElement(dest);
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