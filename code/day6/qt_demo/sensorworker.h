#pragma once

#include <QElapsedTimer>
#include <QObject>
#include <QTimer>

class SensorWorker : public QObject
{
    Q_OBJECT
public:
    explicit SensorWorker(QObject *parent = nullptr);
    ~SensorWorker() override;

signals:
    void sensorValue(double value);

public slots:
    void start();
    void stop();

private slots:
    void timerTimeout();

private:
    QTimer *timer = nullptr;
    QElapsedTimer elapsedTimer;
};
