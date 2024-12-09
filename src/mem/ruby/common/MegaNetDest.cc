
// int count() const;
// bool isEmpty() const;
// void resize();

// void print(std::ostream% out) const;
#include "mem/ruby/common/MegaNetDest.hh"

#include <iostream>
#include <algorithm>

namespace gem5
{

namespace ruby
{

MegaNetDest::MegaNestDest() 
{
    resize();
}

void
MegaNetDest::add(int newElement, int index)
{
    m_bits[index].add(newElement);
}

void
MegaNetDest::remove(int index)
{
    m_bits[index].clear();
}

void
MegaNetDest::clear()
{
    for (int i = 0; i < m_bits.size(); i++) {
        m_bits[i].clear();
    }
}



} // namespace ruby
} // namespace gem5