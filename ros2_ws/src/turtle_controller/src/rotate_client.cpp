#include "rclcpp/rclcpp.hpp"
#include "rclcpp_action/rclcpp_action.hpp"
#include "turtlesim/action/rotate_absolute.hpp"

using RotateAbsolute = turtlesim::action::RotateAbsolute;
using GoalHandleRotateAbsolute = rclcpp_action::ClientGoalHandle<RotateAbsolute>;

class RotateClient : public rclcpp::Node
{
public:
    RotateClient()
    : Node("rotate_client")
    {
        client_ = rclcpp_action::create_client<RotateAbsolute>(this, "/turtle1/rotate_absolute");
        if (!client_->wait_for_action_server(std::chrono::seconds(10)))
        {
            RCLCPP_ERROR(this->get_logger(), "Action server not available after waiting");
        }
        RCLCPP_INFO(this->get_logger(), "Rotate client initialized");
    }

    void send_goal()
    {
        auto goal = RotateAbsolute::Goal();
        goal.theta = M_PI / 2;

        auto send_goal_options = rclcpp_action::Client<RotateAbsolute>::SendGoalOptions();
        send_goal_options.goal_response_callback = std::bind(&RotateClient::goal_response_callback, this, std::placeholders::_1);
        send_goal_options.feedback_callback = std::bind(&RotateClient::feedback_callback, this, std::placeholders::_1, std::placeholders::_2);
        send_goal_options.result_callback = std::bind(&RotateClient::result_callback, this, std::placeholders::_1);

        client_->async_send_goal(goal, send_goal_options);
    }

    void goal_response_callback(GoalHandleRotateAbsolute::SharedPtr goal_handle)
    {
        if (!goal_handle)
        {
            RCLCPP_ERROR(this->get_logger(), "Goal was rejected by server");
        }
        else
        {
            goal_handle_ = goal_handle;
        }
    }

    void feedback_callback(GoalHandleRotateAbsolute::SharedPtr, const std::shared_ptr<const RotateAbsolute::Feedback> feedback)
    {
        RCLCPP_INFO(this->get_logger(), "Received feedback: %f", feedback->remaining);
    }
    
    void result_callback(const GoalHandleRotateAbsolute::WrappedResult& result)
    {
        switch (result.code)
        {
            case rclcpp_action::ResultCode::SUCCEEDED:
                RCLCPP_INFO(this->get_logger(), "Goal succeeded");
                break;
            case rclcpp_action::ResultCode::ABORTED:
                RCLCPP_ERROR(this->get_logger(), "Goal aborted");
                break;
            case rclcpp_action::ResultCode::CANCELED:
                RCLCPP_ERROR(this->get_logger(), "Goal canceled");
                break;
            case rclcpp_action::ResultCode::UNKNOWN:
                RCLCPP_ERROR(this->get_logger(), "Goal unknown");
                break;
            default:
                RCLCPP_ERROR(this->get_logger(), "Goal failed with unknown result code");
                break;
        }
        goal_handle_.reset();
    }

    void cancel_goal()
    {
        if (goal_handle_)
        {
            RCLCPP_INFO(this->get_logger(), "Canceling goal");
            client_->async_cancel_goal(goal_handle_);
        }
        else
        {
            RCLCPP_INFO(this->get_logger(), "No goal to cancel");
        }
    }

private:
    rclcpp_action::Client<RotateAbsolute>::SharedPtr client_;
    GoalHandleRotateAbsolute::SharedPtr goal_handle_;
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<RotateClient>();
    node->send_goal();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}