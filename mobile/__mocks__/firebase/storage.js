module.exports = {
  getStorage: jest.fn(() => ({})),
  ref: jest.fn(),
  uploadBytesResumable: jest.fn(),
  getDownloadURL: jest.fn(),
};
