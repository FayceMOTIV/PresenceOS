module.exports = {
  openAuthSessionAsync: jest.fn().mockResolvedValue({ type: "success" }),
  openBrowserAsync: jest.fn().mockResolvedValue({ type: "opened" }),
};
