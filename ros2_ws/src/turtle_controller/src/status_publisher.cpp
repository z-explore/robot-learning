#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "robot_interfaces/msg/robot_status.hpp"
#include "robot_interfaces/srv/set_mode.hpp"

using RobotStatus = robot_interfaces::msg::RobotStatus;
using SetMode = robot_interfaces::srv::SetMode;
class StatusPublisher : public rclcpp::Node
{
public:
    StatusPublisher():Node("status_publisher")
    {
        status_publisher_ = this->create_publisher<RobotStatus>("/robot_status", 10);
        twist_subscription_ = this->create_subscription<geometry_msgs::msg::Twist>("/turtle1/cmd_vel", 10, std::bind(&StatusPublisher::twistCallback, this, std::placeholders::_1));
        // 2 Hz发布状态
        timer_ = this->create_wall_timer(std::chrono::milliseconds(500),std::bind(&StatusPublisher::publishStatus, this));

        // 新增服务
        set_mode_service_ = this->create_service<SetMode>("/set_mode", std::bind(&StatusPublisher::setModeCallback, this, std::placeholders::_1, std::placeholders::_2));
    }
    
private:

    void setModeCallback(const SetMode::Request::SharedPtr request, SetMode::Response::SharedPtr response)
    {
        RCLCPP_INFO(this->get_logger(), "request: change mode %d to %d", mode_, request->mode);
        // 规则 1: 模式值超出范围
        if(request->mode < RobotStatus::MODE_IDLE || request->mode > RobotStatus::MODE_ESTOP)
        {
            response->success = false;
            response->message = "Invalid mode value";
            return;
        }
        // 规则 2: 急停状态下，不能直接切到自动。
        if(mode_ == RobotStatus::MODE_MANUAL && request->mode == RobotStatus::MODE_ESTOP)
        {
            response->success = false;
            response->message = "Cannot change to automatic mode from emergency stop state";
            return;
        }

        // 通过检查修改模式
        mode_ = request->mode;
        response->success = true;
        response->message = "Mode changed successfully";
    }

    void twistCallback(const geometry_msgs::msg::Twist::SharedPtr msg)
    {
        linear_speed_ = msg->linear.x;
        angular_speed_ = msg->angular.z;
        has_cmd_ = true;
        last_cmd_time_ = this->now();
        RCLCPP_INFO(this->get_logger(), "Received twis  t: linear=%.1f, angular=%.1f", msg->linear.x, msg->angular.z);
    }

    void publishStatus()
    {
        bool moving = has_cmd_ && (this->now() - last_cmd_time_).seconds() < 1.0;
        RobotStatus msg;
        msg.header.stamp = this->now();
        msg.mode = mode_;
        battery_ = std::max(0.0f, battery_ - 0.5f);
        msg.battery_percent = battery_;
        msg.linear_speed = linear_speed_;
        msg.angular_speed = angular_speed_;
        msg.emergency_stop = (mode_ == RobotStatus::MODE_ESTOP);
        msg.message = moving? "RUNNING" : (mode_ == RobotStatus::MODE_ESTOP? "EMERGENCY STOP" : "IDLE");
        status_publisher_->publish(msg);
    }
    rclcpp::Publisher<RobotStatus>::SharedPtr status_publisher_;
    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr twist_subscription_;
    rclcpp::TimerBase::SharedPtr timer_;
    rclcpp::Service<SetMode>::SharedPtr set_mode_service_;
    uint8_t mode_= RobotStatus::MODE_IDLE;
    float battery_= 100;
    float linear_speed_= 0.0f;
    float angular_speed_= 0.0f;
    bool has_cmd_= false;
    rclcpp::Time last_cmd_time_= rclcpp ::Time(0);
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<StatusPublisher>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}