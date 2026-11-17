#include "rclcpp/rclcpp.hpp"
#include "robot_interfaces/msg/robot_status.hpp"

using RobotStatus = robot_interfaces::msg::RobotStatus;

class StatusMonitor : public rclcpp::Node
{
public:
    StatusMonitor():Node("status_monitor")
    {
        status_subscription_ = this->create_subscription<RobotStatus>("/robot_status", 10, std::bind(&StatusMonitor::statusCallback, this, std::placeholders::_1));
    }

private:

    void statusCallback(const RobotStatus::SharedPtr msg)
    {
        if(msg->emergency_stop || msg->mode == RobotStatus::MODE_ESTOP)
        {
            RCLCPP_ERROR(this->get_logger(), "[%s] Emergency stop or ESTOP detected. Stopping the robot.",mode_name(msg->mode));
        }else if(msg->battery_percent < 20.0f)
        {
            RCLCPP_WARN(this->get_logger(), "[%s] Low battery: %.1f. Stopping the robot.",mode_name(msg->mode), msg->battery_percent);
        }
        RCLCPP_INFO(this->get_logger(), "Received status: mode=%d, battery=%.1f, linear_speed=%.1f, angular_speed=%.1f, message=%s", msg->mode, msg->battery_percent, msg->linear_speed, msg->angular_speed, msg->message.c_str());
    }

    const char* mode_name(uint8_t mode)
    {
        switch(mode)
        {
            case RobotStatus::MODE_IDLE: return "IDLE";
            case RobotStatus::MODE_AUTO: return "AUTO";
            case RobotStatus::MODE_MANUAL: return "MANUAL";
            case RobotStatus::MODE_ESTOP: return "ESTOP";
            default: return "UNKNOWN";
        }
    }

    rclcpp::Subscription<RobotStatus>::SharedPtr status_subscription_;
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<StatusMonitor>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}