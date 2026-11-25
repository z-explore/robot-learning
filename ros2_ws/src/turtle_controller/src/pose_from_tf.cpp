#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/transform_stamped.hpp"
#include "tf2_ros/transform_listener.h"
#include "tf2_ros/buffer.h"
#include "tf2/exceptions.h"

class PoseFromTf : public rclcpp::Node
{
public:
    PoseFromTf() : Node("pose_from_tf")
    {
        tf_buffer_ = std::make_unique<tf2_ros::Buffer>(this->get_clock());
        tf_listener_ = std::make_shared<tf2_ros::TransformListener>(*tf_buffer_);

        // 10Hz 查询一次：车在 odom 坐标系下的位置
        timer_ = this->create_wall_timer(
            std::chrono::milliseconds(100),
            std::bind(&PoseFromTf::onTimer, this));

        RCLCPP_INFO(this->get_logger(), "PoseFromTf started, looking up odom -> base_footprint");
    }

private:
    void onTimer()
    {
        geometry_msgs::msg::TransformStamped t;
        try {
            // 目标系 odom，源系 base_footprint：得到「车相对 odom 的位姿」
            t = tf_buffer_->lookupTransform(
                "odom", "base_footprint", tf2::TimePointZero);
        } catch (const tf2::TransformException & ex) {
            RCLCPP_WARN(this->get_logger(), "Could not transform: %s", ex.what());
            return;
        }

        const auto & p = t.transform.translation;
        RCLCPP_INFO(
            this->get_logger(),
            "Robot pose in odom: x=%.3f, y=%.3f, z=%.3f",
            p.x, p.y, p.z);
    }

    std::unique_ptr<tf2_ros::Buffer> tf_buffer_;
    std::shared_ptr<tf2_ros::TransformListener> tf_listener_;
    rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<PoseFromTf>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
