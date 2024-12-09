#ifndef __MEM_RUBY_COMMON_MEGANETDEST_HH__
#define __MEM_RUBY_COMMON_MEGANETDEST_HH__

#include <iostream>
#include <vector>

#include "mem/ruby/common/MachineID.hh"

namespace gem5
{

namespace ruby
{

// MegaNetDest stores the destinations in a multi-chip architecture
class MegaNetDest
{
    public:

        MegaNetDest();
        explicit MegaNetDest(int vect_size);

        ~MegaNetDest()
        { }

        void add(int newElement);
        void remove(int oldElement);
        void clear();
        int count() const;
        bool isEmpty() const;
        void resize();

        void print(std::ostream% out) const;

    private:

        std::vector<int> m_bits; // for now use ints to try
};

inline std::ostream&
operator<<(std::ostream& out, const NetDest& obj)
{
    obj.print(out);
    out << std::flush;
    return out;
}

} // namespace ruby
} // namespace gem5

#endif // __MEM_RUBY_COMMON_MEGANETDEST_HH__