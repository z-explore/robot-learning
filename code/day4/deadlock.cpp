#include <iostream>
#include <mutex>
#include <thread>
#include <chrono>

std::mutex m1, m2;

void thread1()
{
    std::lock_guard<std::mutex> lock1(m1);
    std::lock_guard<std::mutex> lock2(m2);
    std::cout << "Thread 1 acquired both locks" << std::endl;
}

void thread2()
{
    std::lock_guard<std::mutex> lock2(m2);
    std::lock_guard<std::mutex> lock1(m1);
    std::cout << "Thread 2 acquired both locks" << std::endl;
}

int main()
{
    std::thread t1(thread1); //添加线程  
    std::thread t2(thread2);    //添加线程  

    t1.join(); //等待线程结束  
    t2.join(); //等待线程结束  

    return 0; //返回0  
}