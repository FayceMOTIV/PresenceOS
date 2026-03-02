module.exports = {
  useNavigation: jest.fn(() => ({
    navigate: jest.fn(),
    goBack: jest.fn(),
    getParent: jest.fn(() => ({ navigate: jest.fn() })),
  })),
  useRoute: jest.fn(() => ({ params: {} })),
  useFocusEffect: jest.fn((cb) => cb()),
  createNavigationContainerRef: jest.fn(() => ({
    current: null,
    isReady: jest.fn(() => true),
    navigate: jest.fn(),
  })),
};
