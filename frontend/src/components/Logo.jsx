import logoWordmark from "../assets/logo-wordmark.png";

export default function Logo({ size = 40 }) {
  return (
    <img
      src={logoWordmark}
      alt="SmartStock"
      style={{ height: size, width: "auto" }}
    />
  );
}