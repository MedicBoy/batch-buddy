import SwiftUI

struct BatchAlertView: View {
    var pay: String
    var distance: String
    var net: String
    var hourly: String
    var recommendation: String
    
    var onAccept: () -> Void
    var onIgnore: () -> Void
    
    var body: some View {
        ZStack {
            // Dimmed background
            Color.black.opacity(0.6).edgesIgnoringSafeArea(.all)
            
            // The Centered Popup Card
            VStack(spacing: 12) {
                Text("Instacart batch")
                    .font(.title2).bold()
                    .foregroundColor(.white)
                
                Text("\(distance) • 2 stores • 18 items")
                    .font(.subheadline)
                    .foregroundColor(.gray)
                
                Text(pay)
                    .font(.system(size: 45, weight: .bold))
                    .foregroundColor(.white)
                    .padding(.vertical, 5)
                
                HStack {
                    VStack {
                        Text("Net").font(.caption).foregroundColor(.gray)
                        Text(net).font(.headline).foregroundColor(.white)
                    }
                    Spacer()
                    VStack {
                        Text("Hourly").font(.caption).foregroundColor(.gray)
                        Text(hourly).font(.headline).foregroundColor(.white)
                    }
                }
                .padding(.horizontal, 40)
                .padding(.bottom, 10)
                
                HStack(spacing: 12) {
                    Button(action: onIgnore) {
                        Text("Ignore")
                            .font(.headline)
                            .foregroundColor(.white)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color(white: 0.2))
                            .cornerRadius(12)
                    }
                    
                    Button(action: onAccept) {
                        Text("Accept")
                            .font(.headline)
                            .foregroundColor(.black)
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(Color.green)
                            .cornerRadius(12)
                    }
                }
            }
            .padding(24)
            .background(Color(red: 0.11, green: 0.11, blue: 0.12)) // #1C1C1E
            .cornerRadius(24)
            .padding(30)
        }
    }
}
