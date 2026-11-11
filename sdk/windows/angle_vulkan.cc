#include "qigao_sdk/windows/angle_vulkan.h"

#include <algorithm>

#include <EGL/eglext.h>
#include <vulkan/vulkan_core.h>

#include "absl/log/absl_log.h"
#include "absl/strings/str_format.h"

namespace mediapipe::sdk {

absl::Status RequireVulkanHardware(EGLDisplay display,
                                  std::span<const uint8_t> expected_uuid) {
  const auto query_display = reinterpret_cast<PFNEGLQUERYDISPLAYATTRIBEXTPROC>(
      eglGetProcAddress("eglQueryDisplayAttribEXT"));
  const auto query_device = reinterpret_cast<PFNEGLQUERYDEVICEATTRIBEXTPROC>(
      eglGetProcAddress("eglQueryDeviceAttribEXT"));
  if (!query_display || !query_device) {
    return absl::UnavailableError("ANGLE EGL device queries are required");
  }
  EGLAttrib device = 0, instance = 0, physical_device = 0, get_proc = 0;
  if (!query_display(display, EGL_DEVICE_EXT, &device) ||
      !query_device(reinterpret_cast<EGLDeviceEXT>(device),
                    EGL_VULKAN_INSTANCE_ANGLE, &instance) ||
      !query_device(reinterpret_cast<EGLDeviceEXT>(device),
                    EGL_VULKAN_PHYSICAL_DEVICE_ANGLE, &physical_device) ||
      !query_device(reinterpret_cast<EGLDeviceEXT>(device),
                    EGL_VULKAN_GET_INSTANCE_PROC_ADDR, &get_proc)) {
    return absl::UnavailableError("ANGLE did not expose its Vulkan device");
  }
  const auto get_instance_proc = reinterpret_cast<PFN_vkGetInstanceProcAddr>(get_proc);
  const auto get_properties = reinterpret_cast<PFN_vkGetPhysicalDeviceProperties2>(
      get_instance_proc(reinterpret_cast<VkInstance>(instance),
                        "vkGetPhysicalDeviceProperties2"));
  if (!get_properties) {
    return absl::UnavailableError("Vulkan device properties are unavailable");
  }
  VkPhysicalDeviceIDProperties id{};
  id.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_ID_PROPERTIES;
  VkPhysicalDeviceProperties2 details{};
  details.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_PROPERTIES_2;
  details.pNext = &id;
  get_properties(reinterpret_cast<VkPhysicalDevice>(physical_device), &details);
  const auto& properties = details.properties;
  // ANGLE can choose a different device if a requested UUID is unavailable.
  if (!expected_uuid.empty() &&
      !std::ranges::equal(expected_uuid, id.deviceUUID)) {
    return absl::UnavailableError("The requested Vulkan GPU UUID is unavailable");
  }
  switch (properties.deviceType) {
    case VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU:
    case VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU:
    case VK_PHYSICAL_DEVICE_TYPE_VIRTUAL_GPU:
      break;
    default:
      return absl::FailedPreconditionError(absl::StrFormat(
          "GPU inference requires a hardware Vulkan device; selected %s (type %d)",
          properties.deviceName, properties.deviceType));
  }
  ABSL_LOG(INFO) << "MediaPipe ANGLE/Vulkan GPU: " << properties.deviceName
                 << ", vendor=" << properties.vendorID
                 << ", device=" << properties.deviceID
                 << ", driver=" << properties.driverVersion;
  return absl::OkStatus();
}

absl::StatusOr<EGLDisplay> CreateAngleVulkanDisplay() {
  const auto get_display = reinterpret_cast<PFNEGLGETPLATFORMDISPLAYEXTPROC>(
      eglGetProcAddress("eglGetPlatformDisplayEXT"));
  if (!get_display) {
    return absl::UnavailableError("ANGLE platform display extension is required");
  }
  const EGLint attributes[] = {
      EGL_PLATFORM_ANGLE_TYPE_ANGLE, EGL_PLATFORM_ANGLE_TYPE_VULKAN_ANGLE,
      EGL_PLATFORM_ANGLE_DEVICE_TYPE_ANGLE, EGL_PLATFORM_ANGLE_DEVICE_TYPE_HARDWARE_ANGLE,
      EGL_NONE};
  EGLDisplay display = get_display(EGL_PLATFORM_ANGLE_ANGLE,
                                   EGL_DEFAULT_DISPLAY, attributes);
  EGLint major = 0, minor = 0;
  if (display == EGL_NO_DISPLAY || !eglInitialize(display, &major, &minor)) {
    return absl::UnavailableError(absl::StrFormat(
        "Unable to initialize hardware ANGLE/Vulkan: EGL error 0x%X", eglGetError()));
  }
  const absl::Status hardware = RequireVulkanHardware(display);
  if (!hardware.ok()) return hardware;
  return display;
}

}  // namespace mediapipe::sdk
