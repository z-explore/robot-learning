#include "sensorworker.h"

#include <cmath>

SensorWorker::SensorWorker(QObject *parent)
    : QObject(parent)
{
    timer = new QTimer(this);
    connect(timer, &QTimer::timeout, this, &SensorWorker::timerTimeout);
}

SensorWorker::~SensorWorker() = default;

void SensorWorker::start()
{
    elapsedTimer.start();
    timer->start(100);
}

void SensorWorker::stop()
{
    timer->stop();
}

void SensorWorker::timerTimeout()
{
    const double seconds = elapsedTimer.elapsed() / 1000.0;
    emit sensorValue(std::sin(seconds));
}
