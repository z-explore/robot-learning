#include "rclcpp/rclcpp.hpp"
#include "turtlesim/msg/pose.hpp"

class PoseListener : public rclcpp::Node
{
public:
    PoseListener():Node("pose_listener")
    {
        subscription_ = this->create_subscription<turtlesim::msg::Pose>("/turtle1/pose", 10, std::bind(&PoseListener::poseCallBack, this, std::placeholders::_1));
        RCLCPP_INFO(this->get_logger(), "Pose listener has been initialized");
    }

private:
    void poseCallBack(const turtlesim::msg::Pose::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Turtle pose: x=%.2f, y=%.2f, theta=%.2f", msg->x, msg->y, msg->theta);
    }

    rclcpp::Subscription<turtlesim::msg::Pose>::SharedPtr subscription_;
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<PoseListener>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}