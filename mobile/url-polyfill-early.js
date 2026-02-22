// Early URL polyfill — loaded before all other modules
// Patches URL.prototype.protocol to be writable (Hermes makes it read-only)
(function () {
  if (typeof URL !== "undefined") {
    const desc = Object.getOwnPropertyDescriptor(URL.prototype, "protocol");
    if (desc && desc.get && !desc.set) {
      const originalGet = desc.get;
      Object.defineProperty(URL.prototype, "protocol", {
        get: originalGet,
        set: function (value) {
          // Create a new URL with the modified protocol
          const newUrl = new URL(this.href);
          // We can't actually set it on the native Hermes URL,
          // so we store it as a private property
          Object.defineProperty(this, "_protocol", {
            value: value,
            writable: true,
            configurable: true,
          });
        },
        configurable: true,
      });
    }
  }
})();
