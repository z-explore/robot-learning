#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "turtlesim/msg/pose.hpp"

#include <cmath>
#include <vector>

enum class PoseState {
    TURN,     // 在角上原地转到下一条边的方向
    FORWARD   // 沿着这条边的固定方向直走
};

struct Point2d
{
    double x;
    double y;
    Point2d(double x, double y) : x(x), y(y) {}
};

class SquareWalker : public rclcpp::Node
{
public:
    SquareWalker():Node("square_walker")
    {
        twist_publisher_ = this->create_publisher<geometry_msgs::msg::Twist>("/turtle1/cmd_vel", 10);
        subscription_ = this->create_subscription<turtlesim::msg::Pose>("/turtle1/pose", 10, std::bind(&SquareWalker::poseCallBack, this, std::placeholders::_1));
        //path of the_square
        points_.push_back(Point2d{10, 5.544445});
        points_.push_back(Point2d{10, 0.544445});
        points_.push_back(Point2d{5.544445, 0.544445});
        points_.push_back(Point2d{5.544445, 5.544445});

        timer_ = this->create_wall_timer(std::chrono::milliseconds(50), [this]() {
            if(current_pose_ == nullptr)
            {
                return;
            }
            updateState();
            walkSquare();
            // count_++;
            // RCLCPP_INFO(this->get_logger(), "Publishing #%ld: geometry_msgs::msg::Twist(linear=geometry_msgs::msg::Vector3(x=%.1f, y=0.0, z=0.0), angular=geometry_msgs::msg::Vector3(x=0.0, y=0.0, z=%.1f))", count_, twist_msg_.linear.x, twist_msg_.angular.z);
        });
    }

private:
    void poseCallBack(const turtlesim::msg::Pose::SharedPtr msg)
    {
        current_pose_ = msg;
    }

    // 把角度差折回 [-π, π]，朝西时 θ 在 π 和 -π 之间跳也不会被当成差了一整圈。
    static double normalizeAngle(double angle)
    {
        return std::atan2(std::sin(angle), std::cos(angle));
    }

    static double clamp(double value, double low, double high)
    {
        if(value < low) return low;
        if(value > high) return high;
        return value;
    }

    const Point2d& goal() const
    {
        return points_[index_of_point];
    }

    const Point2d& previousCorner() const
    {
        int prev = index_of_point - 1;
        if(prev < 0)
        {
            prev = static_cast<int>(points_.size()) - 1;
        }
        return points_[prev];
    }

    // 边的方向只由两个角点决定，不跟着乌龟的实际位置变。
    double edgeYaw() const
    {
        return std::atan2(goal().y - previousCorner().y, goal().x - previousCorner().x);
    }

    double edgeLength() const
    {
        double dx = goal().x - previousCorner().x;
        double dy = goal().y - previousCorner().y;
        return std::hypot(dx, dy);
    }

    // 从这条边的起点算，已经沿着边走了多远。
    double distanceAlongEdge() const
    {
        double yaw = edgeYaw();
        double dx = current_pose_->x - previousCorner().x;
        double dy = current_pose_->y - previousCorner().y;
        return dx * std::cos(yaw) + dy * std::sin(yaw);
    }

    double yawError() const
    {
        return normalizeAngle(edgeYaw() - current_pose_->theta);
    }

    void updateState()
    {
        double remaining = edgeLength() - distanceAlongEdge();
        if(state_ == PoseState::FORWARD && remaining < arrive_distance_)
        {
            RCLCPP_INFO(this->get_logger(), "到达角点 %d，转向下一条边", index_of_point);
            index_of_point = (index_of_point + 1) % static_cast<int>(points_.size());
            state_ = PoseState::TURN;
            return;
        }

        if(state_ == PoseState::TURN && std::fabs(yawError()) < yaw_tolerance_)
        {
            RCLCPP_INFO(this->get_logger(), "已对准第 %d 条边，开始直行", index_of_point);
            state_ = PoseState::FORWARD;
        }
    }

    void walkSquare()
    {
        double error = yawError();
        if(state_ == PoseState::TURN)
        {
            // 误差越小转得越慢，避免固定角速度一下子转过对准窗口。
            publishTwist(0.0, clamp(yaw_kp_ * error, -max_angular_, max_angular_));
            return;
        }

        double remaining = edgeLength() - distanceAlongEdge();
        double linear = clamp(remaining, min_linear_, max_linear_);
        double angular = clamp(yaw_kp_ * error, -cruise_angular_, cruise_angular_);
        publishTwist(linear, angular);
    }

    void publishTwist(double linear, double angular)
    {
        geometry_msgs::msg::Twist twist_msg;
        twist_msg.linear.x = linear;
        twist_msg.angular.z = angular;
        twist_publisher_->publish(twist_msg);
    }

    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr twist_publisher_;
    rclcpp::Subscription<turtlesim::msg::Pose>::SharedPtr subscription_;
    rclcpp::TimerBase::SharedPtr timer_;
    std::vector<Point2d> points_;
    PoseState state_ = PoseState::TURN;
    turtlesim::msg::Pose::SharedPtr current_pose_;
    int index_of_point = 0;

    double yaw_kp_ = 2.0;
    double max_angular_ = 1.2;
    double cruise_angular_ = 0.4;
    double max_linear_ = 1.0;
    double min_linear_ = 0.2;
    double yaw_tolerance_ = 0.03;
    double arrive_distance_ = 0.05;
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<SquareWalker>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
