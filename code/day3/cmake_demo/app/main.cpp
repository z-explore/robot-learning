#include <iostream>
#include <thread>
#include <functional>
#include "mymath.h"
#include "producer.h"

int main(){
	SharedState state;

	std::thread producerThread(producer, std::ref(state));
	std::thread consumerThread(consumer, std::ref(state));

	producerThread.join();
	consumerThread.join();
}