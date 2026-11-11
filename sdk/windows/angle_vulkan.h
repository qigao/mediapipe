#ifndef QIGAO_MEDIAPIPE_ANGLE_VULKAN_H_
#define QIGAO_MEDIAPIPE_ANGLE_VULKAN_H_

#include <EGL/egl.h>
#include "absl/status/status.h"
#include "absl/status/statusor.h"

namespace mediapipe::sdk {
absl::StatusOr<EGLDisplay> CreateAngleVulkanDisplay();
absl::Status RequireVulkanHardware(EGLDisplay display);
}  // namespace mediapipe::sdk

#endif
