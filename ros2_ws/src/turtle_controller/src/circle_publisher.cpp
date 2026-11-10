#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"
#include "geometry_msgs/msg/twist.hpp"

class CirclePublisher : public rclcpp::Node
{
public:
    CirclePublisher():Node("circle_publisher")
    {
        twist_publisher_ = this->create_publisher<geometry_msgs::msg::Twist>("/turtle1/cmd_vel", 10);
        timer_ = this->create_wall_timer(std::chrono::milliseconds(100), [this]() {
            geometry_msgs::msg::Twist twist_msg_ = geometry_msgs::msg::Twist();
            twist_msg_.linear.x = 2.0;
            twist_msg_.angular.z = 1.8;
            twist_msg_.linear.y = 0.0;
            twist_publisher_->publish(twist_msg_);
            count_++;
            RCLCPP_INFO(this->get_logger(), "Publishing #%ld: geometry_msgs::msg::Twist(linear=geometry_msgs::msg::Vector3(x=%.1f, y=0.0, z=0.0), angular=geometry_msgs::msg::Vector3(x=0.0, y=0.0, z=%.1f))", count_, twist_msg_.linear.x, twist_msg_.angular.z);
        });
    }
private:
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr twist_publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
    size_t count_ = 0;
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<CirclePublisher>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
