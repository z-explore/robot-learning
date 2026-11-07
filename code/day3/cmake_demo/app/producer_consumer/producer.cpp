#include "producer.h"

#include "mymath.h"

#include <chrono>
#include <condition_variable>
#include <iostream>
#include <mutex>
#include <queue>
#include <thread>

void producer(SharedState& state)
{
	for(int i=0; i<20; ++i){
		int value = add(i, i);
		{
			std::cout <<"Producer: "<<value << std::endl;
			std::lock_guard<std::mutex> lock(state.mutex);
			state.queue.push(value);
		}
		state.condition.notify_one();
		std::this_thread::sleep_for(std::chrono::milliseconds(100));
	}

	{
		std::lock_guard<std::mutex> lock(state.mutex);
		state.producerDone = true;
	}
	state.condition.notify_all();
}

void consumer(SharedState &state)
{
	while(true){
		std::unique_lock<std::mutex> lock(state.mutex);
		state.condition.wait(lock, [&]{
			return !state.queue.empty() || state.producerDone;
		});
		
		
		if(state.queue.empty() && state.producerDone){
			break;
		}

		int value = state.queue.front();
		state.queue.pop();
		lock.unlock();
		std::cout <<"Consumer: "<<value << std::endl;
	}
}