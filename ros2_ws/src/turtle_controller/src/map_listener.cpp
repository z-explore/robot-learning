#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

class MapListener : public rclcpp::Node
{
public:
    MapListener() : Node("map_listener")
    {
        auto qos = rclcpp::QoS(1).reliable();
        bool t1 = declare_parameter<bool>("transient_local", false);
        if(t1)
        {
            qos.transient_local();
        }

        subscription_ = this->create_subscription<std_msgs::msg::String>("fake_map", qos, std::bind(&MapListener::mapCallback, this, std::placeholders::_1));

        RCLCPP_INFO(this->get_logger(), "Map listener has been initialized");
    }

private:
    void mapCallback(const std_msgs::msg::String::SharedPtr msg)
    {
        RCLCPP_INFO(this->get_logger(), "Received map: %s", msg->data.c_str());
    }

    rclcpp::Subscription<std_msgs::msg::String>::SharedPtr subscription_;
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<MapListener>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}