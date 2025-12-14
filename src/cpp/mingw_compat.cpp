// Compatibility layer for MinGW when linking MSVC-compiled libraries
// This provides __chkstk which is required by MSVC-compiled OpenSSL

#ifdef __MINGW32__
#include <windows.h>

// __chkstk is a stack probe function used by MSVC
// MSVC-compiled libraries expect this function
// MinGW on x86_64 uses ___chkstk_ms (three underscores)
// We provide a compatibility wrapper

extern "C" {
    // MinGW's version of __chkstk (x86_64 uses three underscores)
    void ___chkstk_ms(void);
    
    // Provide MSVC-compatible __chkstk that calls MinGW's version
    void __chkstk(void) {
        ___chkstk_ms();
    }
}
#endif // __MINGW32__
