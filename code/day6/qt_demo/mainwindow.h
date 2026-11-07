#pragma once

#include <QMainWindow>
#include <QLabel>
#include <QPushButton>
#include <QThread>

#include "sensorworker.h"

class MainWindow : public QMainWindow
{
    Q_OBJECT
public:
    MainWindow(QWidget *parent = nullptr);
    ~MainWindow() override;

private:
    void setupUi();

    QLabel *label = nullptr;
    QPushButton *startButton = nullptr;
    QPushButton *stopButton = nullptr;
    SensorWorker *sensorWorker = nullptr;
    QThread *workerThread = nullptr;

public slots:
    void start();
    void stop();
    void onSensorValue(double value);
};
