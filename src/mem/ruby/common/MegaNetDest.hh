#ifndef __MEM_RUBY_COMMON_MEGANETDEST_HH__
#define __MEM_RUBY_COMMON_MEGANETDEST_HH__

#include <iostream>
#include <vector>

#include "mem/ruby/common/MachineID.hh"
#include "mem/ruby/common/NetDest.hh"

namespace gem5
{

namespace ruby
{

// MegaNetDest stores the destinations in a multi-chip architecture
class MegaNetDest
{
    public:

        MegaNetDest();

        MegaNetDest& operator=(const Set& obj);

        ~MegaNetDest()
        { }

        // Single destination ops
        void add(int chip, MachineID dest);
        void remove(int chip, MachineID dest);
        bool isPresent(MachineID element) const;

        // bulk ops across chips
        void add(const MegaNetDest& others);
        void remove(const MegaNetDest& other);
        void clear();
        void resize();

        // queries
        int totalCount() const; // Count
        bool isEmpty() const;
        bool isBroadcast() const;
        void print(std::ostream& out) const;

    private:
        int m_numChips;
        std::vector<NetDest> m_data;
};

// TODO: adapt to MegaNetDest 
inline std::ostream&
operator<<(std::ostream& out, const MegaNetDest& obj)
{
    obj.print(out);
    out << std::flush;
    return out;
}

} // namespace ruby
} // namespace gem5

#endif // __MEM_RUBY_COMMON_MEGANETDEST_HH__