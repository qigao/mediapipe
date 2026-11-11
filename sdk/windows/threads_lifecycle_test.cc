#include <threads/threads.h>

#include <atomic>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <thread>

namespace {
void Check(bool condition) {
  if (!condition) std::abort();
}
std::atomic<int> cleaned{0};
std::atomic<int> initialized{0};
std::atomic<bool> detach_ready{false};
once_flag once = ONCE_FLAG_INIT;
tss_t key;
void Cleanup(void*) { cleaned.fetch_add(1, std::memory_order_release); }
void Initialize() { initialized.fetch_add(1); }
int Worker(void* detach) {
  Check(thrd_equal(thrd_current(), thrd_current()));
  call_once(&once, Initialize);
  Check(tss_set(key, reinterpret_cast<void*>(1)) == thrd_success);
  if (detach) {
    while (!detach_ready.load(std::memory_order_acquire)) std::this_thread::yield();
    Check(thrd_detach(thrd_current()) == thrd_success);
  }
  return 73;
}
}  // namespace

int main() {
  Check(tss_create(&key, Cleanup) == thrd_success);
  for (int iteration = 0; iteration < 100; ++iteration) {
    thrd_t thread;
    int result = 0;
    Check(thrd_create(&thread, Worker, nullptr) == thrd_success);
    Check(!thrd_equal(thread, thrd_current()));
    Check(thrd_join(thread, &result) == thrd_success && result == 73);
    Check(cleaned.load(std::memory_order_acquire) == iteration + 1);
  }
  // EGL can also be entered from a Godot/foreign thread. Its exit must run
  // the same cleanup even though Salts did not create the thread.
  std::thread foreign([] { Worker(nullptr); });
  foreign.join();
  Check(cleaned.load(std::memory_order_acquire) == 101);
  thrd_t detached;
  Check(thrd_create(&detached, Worker, reinterpret_cast<void*>(1)) == thrd_success);
  detach_ready.store(true, std::memory_order_release);
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(10);
  while (cleaned.load(std::memory_order_acquire) != 102) {
    Check(std::chrono::steady_clock::now() < deadline);
    std::this_thread::yield();
  }
  Check(initialized.load() == 1);
  tss_delete(key);
  std::puts("Salts threads: join, self-detach, once, and foreign-thread TSS cleanup passed");
}
