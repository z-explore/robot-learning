#include "mainwindow.h"

#include <QHBoxLayout>
#include <QVBoxLayout>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
{
    setupUi();

    sensorWorker = new SensorWorker;
    workerThread = new QThread(this);
    sensorWorker->moveToThread(workerThread);
    connect(sensorWorker, &SensorWorker::sensorValue, this, &MainWindow::onSensorValue);
    workerThread->start();
}

MainWindow::~MainWindow()
{
    QMetaObject::invokeMethod(sensorWorker, &SensorWorker::stop, Qt::BlockingQueuedConnection);
    workerThread->quit();
    workerThread->wait();
    delete sensorWorker;
}

void MainWindow::setupUi()
{
    label = new QLabel(this);
    label->setText("Hello, World!");
    startButton = new QPushButton(this);
    startButton->setText("Start");
    stopButton = new QPushButton(this);
    stopButton->setText("Stop");
    connect(startButton, &QPushButton::clicked, this, &MainWindow::start);
    connect(stopButton, &QPushButton::clicked, this, &MainWindow::stop);

    QWidget *centralWidget = new QWidget(this);
    auto *horizontalLayout = new QHBoxLayout;
    horizontalLayout->addWidget(startButton);
    horizontalLayout->addWidget(stopButton);
    auto *verticalLayout = new QVBoxLayout(centralWidget);
    verticalLayout->addWidget(label);
    verticalLayout->addLayout(horizontalLayout);
    setCentralWidget(centralWidget);
}

void MainWindow::start()
{
    QMetaObject::invokeMethod(sensorWorker, &SensorWorker::start, Qt::QueuedConnection);
}

void MainWindow::stop()
{
    QMetaObject::invokeMethod(sensorWorker, &SensorWorker::stop, Qt::QueuedConnection);
    label->setText("Stopped");
}

void MainWindow::onSensorValue(double value)
{
    label->setText(QString::number(value, 'f', 3));
}
