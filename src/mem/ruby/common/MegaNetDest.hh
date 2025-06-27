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

        // Operations on the MegaNetDest
        void add(int chipID, MachineID dest);
        void mergeMegaNetDest(int chipID, const MegaNetDest& others);
        void remove(int chipID, MachineID dest);
        void remove(const MegaNetDest& other);
        void clear();
        void resize();

        // Use of MegaNetDest
        NetDest extractNetDest(int chipID);
        MegaNetDest addMegaNetDest(MegaNetDest mega);

        MegaNetDest smallestElement() const;
        MegaNetDest smallestElement(MachineType machine) const;

        // queries
        int totalCount() const; // Count
        bool isEmpty() const;
        bool isElement(int chipID, MachineID element) const;
        bool isBroadcast() const;
        void print(std::ostream& out) const;

    private:
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