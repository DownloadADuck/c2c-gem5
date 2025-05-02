
// void print(std::ostream% out) const;
#include "mem/ruby/common/MegaNetDest.hh"

#include <iostream>
#include <algorithm>

namespace gem5
{

namespace ruby
{

MegaNetDest::MegaNetDest(int numChips, int nodesPerNet) 
 : m_numChips(numChips) 
{
    m_data.reserve(numChips);
    for (int i = 0; i < numChips; ++i)
        m_data.emplace_back(nodesPerNet);
}

void
MegaNetDest::add(int chip, MachineID dest) 
{
    assert(chip >= 0 && chip < m_numChips);
    m_data[chip].add(dest);
}

void 
MegaNetDest::remove(int chip, MachineID dest) 
{
    assert(chip >= 0 && chip < m_numChips);
    m_data[chip].remove(dest);
}

void
MegaNetDest::isPresent(int chip, MachineID dest) const 
{

}

void 
MegaNetDest::addMega(const MegaNetDest& mega) 
{

}

void
MegaNetDest::removeMega(const MegaNetDest& mega)
{

}

void
MegaNetDest::clear()
{
    for (int i = 0; i < m_bits.size(); i++) {
        m_bits[i] = 0;
    }
}

int
MegaNetDest::count() const
{
    int counter = 0;
    for (int i = 0; i < m_bits.size(); i++) {
        counter += m_bits[i];
    }
    return counter;
}

bool
MegaNetDest::isEmpty() const
{
    for (int i = 0; i < m_bits.size(); i++) {
        if (!m_bits[i] != 0) {
            return false;
        }
    }
    return true;
}

void
MegaNetDest::print(std::ostream& out) const
{
    out << "[MegaNetDest (" << m_bits.size() << ") ";
    
    for (int i = 0; i < m_bits.size(); i++){
        out << m_bits[i];
    }
}

} // namespace ruby
} // namespace gem5