// Entry point — URL polyfill must load before anything else
// Fixes Hermes "Cannot assign to property 'protocol'" error
import "react-native-url-polyfill/auto";

import { registerRootComponent } from "expo";
import App from "./App";

registerRootComponent(App);
