export const categories = {
  laptop: "Laptops",
  component: "Components",
  electronic: "Devices",
};
export const money = (cents) =>
  new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(
    cents / 100,
  );
