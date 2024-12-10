
// void print(std::ostream% out) const;
#include "mem/ruby/common/MegaNetDest.hh"

#include <iostream>
#include <algorithm>

namespace gem5
{

namespace ruby
{

MegaNetDest::MegaNetDest() 
{
//    resize();
}

void
MegaNetDest::add(int newElement, int index)
{
    if (index >= m_bits.size()) {
        m_bits.resize(index + 1, 0);
    }

    m_bits[index] = newElement;
}

void
MegaNetDest::remove(int index)
{
    m_bits[index] = 0;
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