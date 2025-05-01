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

        explicit MegaNetDest(int numChips, int nodesPerNet);

        ~MegaNetDest()
        { }

        // Single destination ops
        void add(int chip, MachineID dest);
        void remove(int chip, MachineID dest);
        void isPresent(int chip, MachineID dest) const;

        // bulk ops across chips
        void addMega(const MegaNetDest& others);
        void removeMega(const MegaNetDest& other);
        void clear();

        // queries
        int totalCount() const;
        bool isEmpty() const;
        bool isBroadcast() const;
        std::string print() const;

        //void print(std::ostream& out) const;

    private:
        int m_numChips;
        std::vector<NetDest> m_data;
};

//inline std::ostream&
//operator<<(std::ostream& out, const MegaNetDest& obj)
//{
//    obj.print(out);
//    out << std::flush;
//    return out;
//}

} // namespace ruby
} // namespace gem5

#endif // __MEM_RUBY_COMMON_MEGANETDEST_HH__