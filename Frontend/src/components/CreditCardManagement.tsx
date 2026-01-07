"use client";

import React, { useState } from "react";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { useLocale } from "@/utils/useLocaleUtil";
import { UserIcon } from "@/assets/icons/UserIcon";
import { PlusIcon } from "@/assets/icons/PlusIcon";
import { EditIcon } from "@/assets/icons/EditIcon";
import { CreditCardIcon } from "@/assets/icons/CreditCardIcon";

interface CreditCard {
  id: string;
  name: string;
  number: string;
  bank?: string;
  logo?: string;
}

interface BankInfo {
  name: string;
  logo: string;
  pattern: RegExp;
}

const banks: BankInfo[] = [
  { name: "بانک ملی", logo: "🏦", pattern: /^603799|^589210|^627353/ },
  { name: "بانک سپه", logo: "🏛️", pattern: /^589210|^627353/ },
  { name: "بانک ملت", logo: "💳", pattern: /^610433|^991975/ },
  { name: "بانک تجارت", logo: "🏪", pattern: /^627353|^585983/ },
  { name: "بانک صادرات", logo: "🚢", pattern: /^603769|^903769/ },
  { name: "بانک پارسیان", logo: "🌟", pattern: /^622106|^627884/ },
  { name: "بانک پاسارگاد", logo: "🦁", pattern: /^502229|^639347/ },
  { name: "بانک سامان", logo: "⚡", pattern: /^621986/ },
  { name: "بانک شهر", logo: "🏙️", pattern: /^502806|^504706/ },
  { name: "بانک آینده", logo: "🔮", pattern: /^636214/ },
];

const formatCardNumber = (value: string): string => {
  const digits = value.replace(/\D/g, "");
  const limitedDigits = digits.slice(0, 16);
  return limitedDigits.replace(/(\d{4})(?=\d)/g, "$1 ");
};

const detectBank = (cardNumber: string): BankInfo | null => {
  const digits = cardNumber.replace(/\s/g, "");
  if (digits.length < 6) return null;
  const prefix = digits.slice(0, 6);
  for (const bank of banks) {
    if (bank.pattern.test(prefix)) {
      return bank;
    }
  }

  return null;
};

export const CreditCardManagement: React.FC = () => {
  const { messages } = useLocale();

  const [card, setCard] = useState<CreditCard | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [newCardName, setNewCardName] = useState("");
  const [newCardNumber, setNewCardNumber] = useState("");
  const [detectedBank, setDetectedBank] = useState<BankInfo | null>(null);

  const handleCardNumberChange = (value: string) => {
    const formatted = formatCardNumber(value);
    setNewCardNumber(formatted);
    const bank = detectBank(formatted);
    setDetectedBank(bank);
  };

  const saveCard = () => {
    if (!newCardName.trim() || newCardNumber.replace(/\s/g, "").length !== 16) {
      return;
    }

    const savedCard: CreditCard = {
      id: card?.id || Date.now().toString(),
      name: newCardName.trim(),
      number: newCardNumber,
      bank: detectedBank?.name,
      logo: detectedBank?.logo,
    };

    setCard(savedCard);
    setNewCardName("");
    setNewCardNumber("");
    setDetectedBank(null);
    setIsEditing(false);
  };

  const startEditing = () => {
    if (card) {
      setNewCardName(card.name);
      setNewCardNumber(card.number);
      const bank = detectBank(card.number);
      setDetectedBank(bank);
      setIsEditing(true);
    }
  };

  const cancelEdit = () => {
    setIsEditing(false);
    setNewCardName("");
    setNewCardNumber("");
    setDetectedBank(null);
  };

  return (
    <div className="w-full max-w-md mx-auto p-4 space-y-4">
      {isEditing ? (
        <div className="w-full flex flex-col items-center justify-center p-6 rounded-xl bg-gradient-to-br from-gray-100 via-gray-200 to-gray-100 dark:from-gray-600 dark:via-gray-700 dark:to-gray-800 shadow-sm">
          <div className="w-11/12 mt-4">
            <Input
              value={newCardName}
              onChange={(e) => setNewCardName(e.target.value)}
              placeholder={messages["credit-cards-card-holder-placeholder"]}
            />
          </div>

          <div className="w-11/12 my-4">
            <Input
              dir="ltr"
              value={newCardNumber}
              onChange={(e) => handleCardNumberChange(e.target.value)}
              placeholder="0000 0000 0000 0000"
              className="font-mono"
              maxLength={19} // 16 digits + 3 spaces
              addonAfter={
                detectedBank ? (
                  <span className="text-xl">{detectedBank.logo}</span>
                ) : undefined
              }
            />
          </div>

          <div className="flex space-x-2 w-11/12 mt-6 mb-2">
            <Button
              onClick={saveCard}
              disabled={
                !newCardName.trim() ||
                newCardNumber.replace(/\s/g, "").length !== 16 ||
                !detectedBank
              }
              className="flex-1"
              size="lg"
            >
              {messages["credit-cards-save"]}
            </Button>
            <Button
              onClick={cancelEdit}
              variant="outline"
              className="flex-1"
              size="lg"
            >
              {messages["credit-cards-cancel"]}
            </Button>
          </div>
        </div>
      ) : (
        <>
          <div className="space-y-3">
              {!card ? (
                <div className="text-center py-12 text-text-secondary border-2 border-dashed border-text-secondary/20 rounded-lg">
                  <CreditCardIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p className="text-lg font-medium mb-2">
                    {messages["credit-cards-empty"]}
                  </p>
                  <p className="text-sm opacity-75">
                    {messages["credit-cards-empty-desc"]}
                  </p>
                <Button onClick={() => setIsEditing(true)} className="mt-4">
                  <PlusIcon className="w-4 h-4 mr-2" />
                  {messages["credit-cards-add-new"]}
                </Button>
              </div>
            ) : (
              <div className="bg-gradient-to-br from-sky-500 via-sky-600 to-sky-700 rounded-2xl p-6 text-white shadow-2xl relative overflow-hidden transform hover:scale-105 transition-all duration-300 ease-in-out border border-sky-400/30">
                {/* Effect */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent transform -skew-x-12 animate-pulse"></div>
                <div className="relative z-10">
                  <div className="flex justify-between items-start mb-6">
                    <div className="flex items-center space-x-3">
                      {card.logo && (
                        <span className="text-2xl drop-shadow-lg">
                          {card.logo}
                        </span>
                      )}
                      {card.bank && (
                        <span className="text-sm font-medium opacity-90 tracking-wide">
                          {card.bank}
                        </span>
                      )}
                    </div>
                    <Button
                      onClick={startEditing}
                      size="sm"
                      variant="ghost"
                      className="text-white/80 hover:text-white hover:bg-white/10 p-2 h-9 w-9 rounded-full backdrop-blur-sm transition-all duration-200"
                    >
                      <EditIcon className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="mb-6">
                    <p
                      className="text-xl text-center font-mono tracking-[0.2em] font-bold drop-shadow-sm"
                      dir="ltr"
                    >
                      {card.number}
                    </p>
                  </div>
                  <div className="flex justify-between items-end">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-white/60 uppercase tracking-wider">
                        <UserIcon className="stroke-white/60 stroke-3 size-4" />
                      </span>
                      <span className="text-base font-semibold tracking-wide">
                        {card.name}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
};
