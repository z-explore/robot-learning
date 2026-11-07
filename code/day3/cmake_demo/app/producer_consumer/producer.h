#pragma once

#include <condition_variable>
#include <mutex>
#include <queue>

struct SharedState {
    std::queue<int> queue;
    std::mutex mutex;
    std::condition_variable condition;
    bool producerDone = false;
};  

void producer(SharedState &state);

void consumer(SharedState &state);
