#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

class FakeMapPub : public rclcpp::Node
{
public:
    FakeMapPub() : Node("fake_map_pub")
    {
        auto qos = rclcpp::QoS(1).transient_local().reliable();
        publisher_ = this->create_publisher<std_msgs::msg::String>("fake_map", qos);
        std_msgs::msg::String msg;
        msg.data = "map v1";
        publisher_->publish(msg);
        RCLCPP_INFO(this->get_logger(), "Published fake map v1");
    }

private:
    rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<FakeMapPub>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}