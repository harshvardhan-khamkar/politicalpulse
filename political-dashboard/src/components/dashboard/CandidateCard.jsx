import React from 'react';
import clsx from 'clsx';

const CandidateCard = ({ name, party, image, partyLogo, popularity, winRate, polls, trustIndex }) => {
    return (
        <div className="bg-white p-5 rounded-3xl shadow-sm border border-gray-100">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                    <img
                        src={image}
                        alt={name}
                        className="w-10 h-10 rounded-full object-cover border border-gray-100"
                    />
                    <div>
                        <h4 className="font-bold text-gray-900 text-sm">{name}</h4>
                        <p className="text-xs text-gray-500 uppercase">{party}</p>
                    </div>
                </div>
                <img src={partyLogo} alt={party} className="w-6 h-6 object-contain" />
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div>
                    <p className="text-[10px] text-gray-400 uppercase font-semibold mb-1">Popularity</p>
                    <div className="flex items-end gap-1">
                        <span className="text-lg font-bold text-gray-800">{popularity}%</span>
                    </div>
                    <div className="w-full bg-gray-100 h-1 rounded-full mt-1">
                        <div className="bg-orange-400 h-1 rounded-full" style={{ width: `${popularity}%` }}></div>
                    </div>
                </div>

                <div>
                    <p className="text-[10px] text-gray-400 uppercase font-semibold mb-1">Win Rate</p>
                    <div className="flex items-end gap-1">
                        <span className="text-lg font-bold text-gray-800">{winRate}%</span>
                    </div>
                    <div className="w-full bg-gray-100 h-1 rounded-full mt-1">
                        <div className="bg-orange-400 h-1 rounded-full" style={{ width: `${winRate}%` }}></div>
                    </div>
                </div>

                <div>
                    <p className="text-[10px] text-gray-400 uppercase font-semibold mb-1">Polls</p>
                    <div className="flex items-end gap-1">
                        <span className="text-lg font-bold text-gray-800">{polls}%</span>
                    </div>
                    <div className="w-full bg-gray-100 h-1 rounded-full mt-1">
                        <div className="bg-green-600 h-1 rounded-full" style={{ width: `${polls}%` }}></div>
                    </div>
                </div>

                <div>
                    <p className="text-[10px] text-gray-400 uppercase font-semibold mb-1">Trust Index</p>
                    <div className="flex items-end gap-1">
                        <span className="text-lg font-bold text-gray-800">
                            {trustIndex !== undefined ? trustIndex : 50}%
                        </span>
                    </div>
                    <div className="w-full bg-gray-100 h-1 rounded-full mt-1">
                        <div
                            className={`h-1 rounded-full ${trustIndex >= 50 ? 'bg-green-500' : 'bg-red-500'}`}
                            style={{ width: `${trustIndex !== undefined ? trustIndex : 50}%` }}
                        ></div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CandidateCard;
