#ifndef QIGAO_MEDIAPIPE_ANGLE_VULKAN_H_
#define QIGAO_MEDIAPIPE_ANGLE_VULKAN_H_

#include <cstdint>
#include <span>

#include <EGL/egl.h>
#include "absl/status/status.h"
#include "absl/status/statusor.h"

namespace mediapipe::sdk {
absl::StatusOr<EGLDisplay> CreateAngleVulkanDisplay();
absl::Status RequireVulkanHardware(EGLDisplay display,
                                  std::span<const uint8_t> expected_uuid = {});
}  // namespace mediapipe::sdk

#endif
