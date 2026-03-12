import React from "react";
import { Composition } from "remotion";
import {
  RestaurantShowcase,
  RestaurantShowcaseProps,
} from "./templates/RestaurantShowcase";
import { PromoFlash, PromoFlashProps } from "./templates/PromoFlash";
import { DailyStory, DailyStoryProps } from "./templates/DailyStory";
import { BreakoutClip, BreakoutClipProps } from "./templates/BreakoutClip";
import { BreakoutV4, BreakoutV4Props } from "./templates/BreakoutV4";

// Default data for Remotion Studio preview
const defaultRestaurantProps: RestaurantShowcaseProps = {
  brandName: "La Belle Assiette",
  tagline: "Cuisine francaise traditionnelle",
  dishes: [
    {
      name: "Filet de Boeuf",
      image: "https://images.unsplash.com/photo-1546833998-877b37c2e5c6?w=1080",
      description: "Tendre et juteux, sauce au poivre",
    },
    {
      name: "Risotto aux Champignons",
      image: "https://images.unsplash.com/photo-1476124369491-e7addf5db371?w=1080",
      description: "Cremeux a souhait, parmigiano 24 mois",
    },
    {
      name: "Tiramisu Maison",
      image: "https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=1080",
      description: "Notre recette secrete depuis 2010",
    },
  ],
  primaryColor: "#D4A574",
};

const defaultPromoProps: PromoFlashProps = {
  headline: "VENTE FLASH",
  subheadline: "-30% sur toute la carte",
  promoCode: "FLASH30",
  discount: "-30%",
  ctaText: "Reservez maintenant!",
  backgroundImage:
    "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1080",
  primaryColor: "#E63946",
  brandName: "La Belle Assiette",
  validUntil: "31 janvier",
};

const defaultDailyStoryProps: DailyStoryProps = {
  brandName: "La Belle Assiette",
  slides: [
    {
      text: "Bonjour! Voici notre plat du jour",
      image: "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1080",
    },
    {
      text: "Prepare avec amour par notre Chef",
      image: "https://images.unsplash.com/photo-1556910103-1c02745aae4d?w=1080",
    },
    {
      text: "Reservez votre table ce soir!",
      image: "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=1080",
    },
  ],
  primaryColor: "#6C63FF",
};

const defaultBreakoutProps: BreakoutClipProps = {
  originalPhotoUrl:
    "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=1080",
  cutoutUrl:
    "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=1080",
  businessName: "Le Family's",
  likesCount: 1247,
  instagramHandle: "@lefamilys",
  accentColor: "#F59E0B",
};

const defaultBreakoutV4Props: BreakoutV4Props = {
  originalPhotoUrl:
    "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=1080",
  cutoutUrl:
    "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=1080",
  businessName: "Le Family's",
  instagramHandle: "@lefamilys",
  caption: "Notre burger signature, fait maison avec amour !",
  accentColor: "#F59E0B",
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="RestaurantShowcase"
        component={RestaurantShowcase}
        durationInFrames={300}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={defaultRestaurantProps}
      />
      <Composition
        id="PromoFlash"
        component={PromoFlash}
        durationInFrames={240}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={defaultPromoProps}
      />
      <Composition
        id="DailyStory"
        component={DailyStory}
        durationInFrames={270}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={defaultDailyStoryProps}
      />
      <Composition
        id="BreakoutClip"
        component={BreakoutClip}
        durationInFrames={90}
        fps={30}
        width={720}
        height={1280}
        defaultProps={defaultBreakoutProps}
      />
      <Composition
        id="BreakoutV4"
        component={BreakoutV4}
        durationInFrames={90}
        fps={30}
        width={720}
        height={1280}
        defaultProps={defaultBreakoutV4Props}
      />
    </>
  );
};
