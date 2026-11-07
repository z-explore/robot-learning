#include <iostream>
#include <vector>

struct Sensor{
    int id;
    double value;
};

double readSensor(Sensor* s)
{
    return s->value*2;
}

double processAll(std::vector<Sensor*>& sensors)
{
    double sum = 0;
    for(size_t i=0; i<sensors.size(); ++i)
    {
        sum += readSensor(sensors[i]);
    }
    return sum;
}

int main()
{
    Sensor a{1,1.5};
    Sensor b{2,2.5};
    std::vector<Sensor*> sensors{&a,&b,nullptr};
    std::cout<<"sum = "<<processAll(sensors)<<std::endl;
}
